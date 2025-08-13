# services/ai/model_trainer.py - ai-5-4.py에서 학습 관련 기능 분리

import os, glob, json, sys, re
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
from datetime import datetime
import joblib

from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

from dataclasses import dataclass

MODEL_DIR = os.environ.get("MODEL_DIR", "model_all")

# ───────────────────────────── 데이터 정규화 유틸 ─────────────────────────────
def _norm_category(x):
    """카테고리는 DB 값 그대로 사용. None/NaN만 안전처리."""
    if x is None:
        return "Unknown"
    try:
        if isinstance(x, float) and np.isnan(x):
            return "Unknown"
    except Exception:
        pass
    return x

def _norm_size(s) -> str:
    """사이즈 정규화: 숫자만 추출 → 3자리면 0패딩(402→0402), 4자리 이상은 그대로."""
    if s is None:
        return "Unknown"
    txt = str(s).strip()
    if "/" in txt:
        txt = txt.split("/")[0].strip()
    digits = re.sub(r"[^0-9]", "", txt)
    if digits.isdigit():
        return digits.zfill(4) if len(digits) == 3 else digits
    return txt

def _norm_manufacturer(x: str) -> str:
    if x is None:
        return "unknown"
    return str(x).strip()

# ─────────────────────── 데이터 로드/피처 엔지니어링 ───────────────────────
def load_annual_category_data(data_root="data", years=None) -> pd.DataFrame:
    """연도별 파트 데이터 로드 및 피처 엔지니어링"""
    years = years or [2023, 2024]
    frames = []
    
    for yr in years:
        ydir = os.path.join(data_root, str(yr))
        if not os.path.isdir(ydir): 
            continue
        for p in glob.glob(os.path.join(ydir, "Part_*.csv")):
            df = pd.read_csv(p)
            df["year"] = yr
            frames.append(df)
    
    if not frames:
        raise FileNotFoundError("데이터가 없습니다. 2023,2024 CSV를 먼저 준비하세요.")
    
    df = pd.concat(frames, ignore_index=True)
    df["date"] = pd.to_datetime(df["date"])
    df.sort_values(["part_id", "date"], inplace=True)

    # 정규화
    if "category" in df.columns:
        df["category"] = df["category"].map(_norm_category)
    if "size" in df.columns:
        df["size"] = df["size"].map(_norm_size)
    if "manufacturer" in df.columns:
        df["manufacturer"] = df["manufacturer"].map(_norm_manufacturer)

    # 시계열 피처
    df["dow"] = df["date"].dt.dayofweek
    df["month"] = df["date"].dt.month
    df["rolling7_used"] = df.groupby("part_id")["used_actual"].transform(lambda s: s.rolling(7, 1).mean())
    df["rolling30_used"] = df.groupby("part_id")["used_actual"].transform(lambda s: s.rolling(30, 1).mean())
    
    for lag in [1, 7, 30]:
        df[f"lag{lag}_used"] = df.groupby("part_id")["used_actual"].shift(lag).fillna(0)
    
    df["roll7_std_used"] = df.groupby("part_id")["used_actual"].transform(lambda s: s.rolling(7, 1).std().fillna(0))
    df["roll30_std_used"] = df.groupby("part_id")["used_actual"].transform(lambda s: s.rolling(30, 1).std().fillna(0))

    # 소진일/위험
    eps = 1e-5
    df["days_to_zero_est"] = df["closing_stock"] / (df["rolling7_used"] + eps)
    df["risk_6m"] = (df["days_to_zero_est"] <= 183).astype(int)
    df["risk_12m"] = (df["days_to_zero_est"] <= 365).astype(int)

    # 미래 30일 수요(라벨)
    fut = []
    for _, g in df.groupby("part_id"):
        u = g["used_actual"].to_numpy()
        n = len(u)
        fut.extend([u[i+1:i+31].sum() for i in range(n)])
    df["future_30d_used"] = fut

    # horizon 미충족 구간 제거
    df = df.sort_values(["part_id", "date"]).copy()
    df["_row"] = df.groupby("part_id").cumcount()
    df["_n"] = df.groupby("part_id")["part_id"].transform("size")
    df = df[df["_row"] < df["_n"] - 30].drop(columns=["_row", "_n"]).reset_index(drop=True)
    
    return df

def _build_X(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """피처 행렬 구성"""
    base = [
        "opening_stock", "planned_usage", "used_actual", "pending_inbound_before_order",
        "lead_time_days", "dow", "month", "rolling7_used", "rolling30_used",
        "lag1_used", "lag7_used", "lag30_used", "roll7_std_used", "roll30_std_used",
        "unit_price", "monthly_discount", "shipping_fee", "region_fee"
    ]
    X = df[base + ["category", "size", "manufacturer"]].copy()
    X = pd.get_dummies(X, columns=["category", "size", "manufacturer"], drop_first=True)
    return X, list(X.columns)

class ModelTrainer:
    """AI 모델 학습 클래스"""
    
    def __init__(self, model_dir=None):
        self.model_dir = model_dir or MODEL_DIR
        os.makedirs(self.model_dir, exist_ok=True)
    
    def train_and_save_models(self, df_all: pd.DataFrame, args=None) -> str:
        """모델 학습 및 저장"""
        X, feature_columns = _build_X(df_all)
        
        if args and getattr(args, "float32", False):
            X[X.select_dtypes("float64").columns] = X.select_dtypes("float64").astype("float32")

        models_by_group = {}
        rng = np.random.default_rng(42)

        # 평가 수집버킷
        do_eval = bool(getattr(args, "eval_mae", False))
        eval_split = float(getattr(args, "eval_split", 0.2))
        y_true_usage_all, y_pred_usage_all = [], []
        y_true_order_all, y_pred_order_all = [], []
        used_fallback_for_order = False

        for (cat, size, man), g in df_all.groupby(["category", "size", "manufacturer"]):
            idx = g.index
            Xg = X.loc[idx]

            y_u = df_all.loc[idx, "future_30d_used"].values.astype(float)
            y_d = df_all.loc[idx, "days_to_zero_est"].values.astype(float)
            y_6 = df_all.loc[idx, "risk_6m"].values.astype(int)
            y_12 = df_all.loc[idx, "risk_12m"].values.astype(int)

            # 수량 불일치 이벤트(라벨에 8% 확률로 ±3~8% 편차)
            pr = getattr(args, "event_prob", 0.08)
            lo, hi = (0.03, 0.08)
            if getattr(args, "event_range", None): 
                lo, hi = args.event_range
            if len(y_u) > 0:
                m = rng.random(len(y_u)) < pr
                if m.any():
                    noise = rng.uniform(1.0-lo, 1.0+hi, size=int(m.sum()))
                    y_u = y_u.copy()
                    y_u[m] *= noise

            rf_reg = getattr(args, "rf_reg", 200)
            rf_days = getattr(args, "rf_days", 200)
            rf_cls = getattr(args, "rf_cls", 200)
            max_depth = getattr(args, "max_depth", None)

            # 학습/평가 분할(그룹 단위)
            if do_eval and len(idx) >= max(10, int(1.0/eval_split)+5):
                Xtr, Xte, ytr_u, yte_u, ytr_d, yte_d, ytr6, yte6, ytr12, yte12, idx_tr, idx_te = \
                    self._split_many(Xg, y_u, y_d, y_6, y_12, idx, test_size=eval_split, random_state=42)
            else:
                Xtr, Xte = Xg, None
                ytr_u, yte_u = y_u, None
                ytr_d, yte_d = y_d, None
                ytr6, yte6 = y_6, None
                ytr12, yte12 = y_12, None
                idx_tr, idx_te = idx, None

            reg_usage = RandomForestRegressor(n_estimators=rf_reg, max_depth=max_depth, random_state=42, n_jobs=-1).fit(Xtr, ytr_u)
            reg_days = RandomForestRegressor(n_estimators=rf_days, max_depth=max_depth, random_state=42, n_jobs=-1).fit(Xtr, ytr_d)
            cls_6m = RandomForestClassifier(n_estimators=rf_cls, max_depth=max_depth, random_state=42, n_jobs=-1).fit(Xtr, ytr6)
            cls_12m = RandomForestClassifier(n_estimators=rf_cls, max_depth=max_depth, random_state=42, n_jobs=-1).fit(Xtr, ytr12)

            models_by_group[(cat, size, man)] = {
                "reg_usage": reg_usage, "reg_days": reg_days, "cls_6m": cls_6m, "cls_12m": cls_12m
            }

            # 평가: 예측 MAE(30일 수요) + 발주 MAE
            if do_eval and Xte is not None and len(Xte) > 0:
                pred_usage = reg_usage.predict(Xte)
                y_true_usage_all.extend(list(yte_u))
                y_pred_usage_all.extend(list(pred_usage))

                # 발주 Ground Truth
                if "order_qty_effective" in df_all.columns:
                    true_order = df_all.loc[idx_te, "order_qty_effective"].fillna(0).astype(float).values
                else:
                    # Fallback: 실제 30일 수요와 opening_stock으로 현실적 발주량 라벨 생성
                    used_fallback_for_order = True
                    open_stock = df_all.loc[idx_te, "opening_stock"].fillna(0).astype(float).values \
                                 if "opening_stock" in df_all.columns else np.zeros_like(yte_u)
                    true_order = np.array([
                        self._order_from_usage(u30, os_, getattr(args, "service_days", 14),
                                              getattr(args, "horizon", 30), getattr(args, "pack_size", 100))
                        for u30, os_ in zip(yte_u, open_stock)
                    ], dtype=float)

                # 예측 발주량: 예측 usage30 + opening_stock 기반
                open_stock_pred = df_all.loc[idx_te, "opening_stock"].fillna(0).astype(float).values \
                                  if "opening_stock" in df_all.columns else np.zeros_like(pred_usage)
                pred_order = np.array([
                    self._order_from_usage(u30, os_, getattr(args, "service_days", 14),
                                          getattr(args, "horizon", 30), getattr(args, "pack_size", 100))
                    for u30, os_ in zip(pred_usage, open_stock_pred)
                ], dtype=float)

                y_true_order_all.extend(list(true_order))
                y_pred_order_all.extend(list(pred_order))

        # 메타/저장
        meta = {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "train_years": sorted({int(y) for y in df_all["year"].unique()}) if "year" in df_all.columns else [],
            "n_rows": int(len(df_all)),
            "n_parts": int(df_all["part_id"].nunique()),
            "group_count": int(df_all.groupby(["category", "size", "manufacturer"])["part_id"].nunique().shape[0]),
            "feature_count": len(feature_columns),
            "rf_params": {"rf_reg": getattr(args, "rf_reg", 200), "rf_days": getattr(args, "rf_days", 200),
                          "rf_cls": getattr(args, "rf_cls", 200), "max_depth": getattr(args, "max_depth", None)}
        }

        # MAE 출력/기록
        if do_eval and len(y_true_usage_all) > 0 and len(y_true_order_all) > 0:
            usage_mae = float(mean_absolute_error(y_true_usage_all, y_pred_usage_all))
            order_mae = float(mean_absolute_error(y_true_order_all, y_pred_order_all))
            flag = " (fallback GT)" if used_fallback_for_order and "order_qty_effective" not in df_all.columns else ""
            print(f"[eval] 예측 MAE (30일 수요): {usage_mae:.3f}")
            print(f"[eval] 발주 MAE{flag}: {order_mae:.3f}")
            meta["metrics"] = {"usage_mae": usage_mae, "order_mae": order_mae}
        else:
            meta["metrics"] = {}

        bundle = {"feature_columns": feature_columns, "models": models_by_group, "meta": meta}
        path = os.path.join(self.model_dir, "model_bundle.pkl")
        joblib.dump(bundle, path, compress=getattr(args, "compress", 3))
        print(f"[model] 저장: {path}")

        if getattr(args, "save_meta", False):
            with open(os.path.join(self.model_dir, "model_meta.json"), "w", encoding="utf-8") as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
            print("[model] 메타 저장: model_all/model_meta.json")

        return path

    def _split_many(self, Xg, y_u, y_d, y6, y12, idx, test_size=0.2, random_state=42):
        """다중 타겟 분할"""
        Xtr, Xte, ytr_u, yte_u, idx_tr, idx_te = train_test_split(
            Xg, y_u, idx, test_size=test_size, random_state=random_state
        )
        # 같은 분할을 쓰기 위해 인덱스 기반 매핑
        m_tr = pd.Index(Xtr.index)
        m_te = pd.Index(Xte.index)
        ytr_d = pd.Series(y_d, index=Xg.index).loc[m_tr].values
        yte_d = pd.Series(y_d, index=Xg.index).loc[m_te].values
        ytr6 = pd.Series(y6, index=Xg.index).loc[m_tr].values
        yte6 = pd.Series(y6, index=Xg.index).loc[m_te].values
        ytr12 = pd.Series(y12, index=Xg.index).loc[m_tr].values
        yte12 = pd.Series(y12, index=Xg.index).loc[m_te].values
        return Xtr, Xte, ytr_u, yte_u, ytr_d, yte_d, ytr6, yte6, ytr12, yte12, idx_tr, idx_te

    def _order_from_usage(self, usage30: float, opening_stock: float,
                          service_days: int, horizon: int, pack_size: int) -> int:
        """사용량 기반 발주량 계산"""
        need = float(usage30) * (service_days/float(max(horizon, 1))) - float(opening_stock)
        if pack_size > 0 and need > 0:
            return int(np.ceil(need/pack_size)*pack_size)
        return int(max(0.0, need))
