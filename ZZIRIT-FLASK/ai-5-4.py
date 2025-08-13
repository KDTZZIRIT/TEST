# ai-5-4.py — 2023/2024 학습 + DB/CSV 추론 + 최적 발주 Top-3
# + 확률 이벤트(8%) + ai-5-3 스타일 요약 출력
# + ★ 평가 옵션 추가: --eval-mae --eval-split
# ====================================================================================
# 사용 예시)
#   1) 학습(+MAE평가):       python ai-5-4.py --retrain --years 2023,2024 --eval-mae --eval-split 0.2
#   2) 학습 후 DB로 추론:     python ai-5-4.py --predict --from-db
#   3) 학습 후 CSV로 추론:    python ai-5-4.py --predict --from-csv data/snapshot_today.csv
# 정책/옵션)
#   --event-prob 0.08  --event-range 0.03 0.08
#   --allow-negative-in-calc  (계산 단계에서 음수 재고 허용; 기본은 0으로 클립)
#   --save-meta               (model_meta.json 저장; 기본은 저장 안 함)
# ====================================================================================

import os, glob, json, argparse, sys, re
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
from datetime import datetime
import joblib

from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

MODEL_DIR = "model_all"
os.makedirs(MODEL_DIR, exist_ok=True)

# ───────────────────────────── 공통 유틸 ─────────────────────────────
def _print(s=""):
    print(s); sys.stdout.flush()

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
def load_annual_category_data(data_root="data", years=None)->pd.DataFrame:
    years = years or [2023, 2024]
    frames=[]
    for yr in years:
        ydir=os.path.join(data_root,str(yr))
        if not os.path.isdir(ydir): continue
        for p in glob.glob(os.path.join(ydir,"Part_*.csv")):
            df=pd.read_csv(p)
            df["year"]=yr
            frames.append(df)
    if not frames:
        raise FileNotFoundError("데이터가 없습니다. 2023,2024 CSV를 먼저 준비하세요.")
    df=pd.concat(frames,ignore_index=True)

    df["date"]=pd.to_datetime(df["date"])
    df.sort_values(["part_id","date"],inplace=True)

    # 그대로 사용(Null만 처리)
    if "category" in df.columns:
        df["category"]=df["category"].map(_norm_category)
    if "size" in df.columns:
        df["size"]=df["size"].map(_norm_size)
    if "manufacturer" in df.columns:
        df["manufacturer"]=df["manufacturer"].map(_norm_manufacturer)

    # 시계열 피처
    df["dow"]=df["date"].dt.dayofweek
    df["month"]=df["date"].dt.month
    df["rolling7_used"]=df.groupby("part_id")["used_actual"].transform(lambda s:s.rolling(7,1).mean())
    df["rolling30_used"]=df.groupby("part_id")["used_actual"].transform(lambda s:s.rolling(30,1).mean())
    for lag in [1,7,30]:
        df[f"lag{lag}_used"]=df.groupby("part_id")["used_actual"].shift(lag).fillna(0)
    df["roll7_std_used"]=df.groupby("part_id")["used_actual"].transform(lambda s:s.rolling(7,1).std().fillna(0))
    df["roll30_std_used"]=df.groupby("part_id")["used_actual"].transform(lambda s:s.rolling(30,1).std().fillna(0))

    # 소진일/위험
    eps=1e-5
    df["days_to_zero_est"]=df["closing_stock"]/(df["rolling7_used"]+eps)
    df["risk_6m"]=(df["days_to_zero_est"]<=183).astype(int)
    df["risk_12m"]=(df["days_to_zero_est"]<=365).astype(int)

    # 미래 30일 수요(라벨)
    fut=[]
    for _,g in df.groupby("part_id"):
        u=g["used_actual"].to_numpy()
        n=len(u)
        fut.extend([u[i+1:i+31].sum() for i in range(n)])
    df["future_30d_used"]=fut

    # horizon 미충족 구간 제거
    df = df.sort_values(["part_id","date"]).copy()
    df["_row"] = df.groupby("part_id").cumcount()
    df["_n"]   = df.groupby("part_id")["part_id"].transform("size")
    df = df[df["_row"] < df["_n"] - 30].drop(columns=["_row","_n"]).reset_index(drop=True)
    return df

# ─────────────────────────── 학습 (그룹별 모델) ───────────────────────────
def _build_X(df:pd.DataFrame)->Tuple[pd.DataFrame,List[str]]:
    base=[
        "opening_stock","planned_usage","used_actual","pending_inbound_before_order",
        "lead_time_days","dow","month","rolling7_used","rolling30_used",
        "lag1_used","lag7_used","lag30_used","roll7_std_used","roll30_std_used",
        "unit_price","monthly_discount","shipping_fee","region_fee"
    ]
    X=df[base+["category","size","manufacturer"]].copy()
    X=pd.get_dummies(X,columns=["category","size","manufacturer"],drop_first=True)
    return X, list(X.columns)

def _order_from_usage(usage30: float, opening_stock: float,
                      service_days: int, horizon: int, pack_size: int) -> int:
    need = float(usage30) * (service_days/float(max(horizon,1))) - float(opening_stock)
    if pack_size>0 and need>0:
        return int(np.ceil(need/pack_size)*pack_size)
    return int(max(0.0, need))

def train_and_save_models(df_all:pd.DataFrame, out_dir=MODEL_DIR, args=None)->str:
    X, feature_columns = _build_X(df_all)
    if args and getattr(args, "float32", False):
        X[X.select_dtypes("float64").columns]=X.select_dtypes("float64").astype("float32")

    models_by_group={}
    rng=np.random.default_rng(42)

    # 평가 수집버킷
    do_eval = bool(getattr(args, "eval_mae", False))
    eval_split = float(getattr(args, "eval_split", 0.2))
    y_true_usage_all, y_pred_usage_all = [], []
    y_true_order_all, y_pred_order_all = [], []
    used_fallback_for_order = False

    for (cat,size,man), g in df_all.groupby(["category","size","manufacturer"]):
        idx=g.index
        Xg=X.loc[idx]

        y_u=df_all.loc[idx,"future_30d_used"].values.astype(float)
        y_d=df_all.loc[idx,"days_to_zero_est"].values.astype(float)
        y_6=df_all.loc[idx,"risk_6m"].values.astype(int)
        y_12=df_all.loc[idx,"risk_12m"].values.astype(int)

        # 수량 불일치 이벤트(라벨에 8% 확률로 ±3~8% 편차)
        pr=getattr(args,"event_prob",0.08)
        lo,hi=(0.03,0.08)
        if getattr(args,"event_range",None): lo,hi=args.event_range
        if len(y_u)>0:
            m = rng.random(len(y_u)) < pr
            if m.any():
                noise = rng.uniform(1.0-lo, 1.0+hi, size=int(m.sum()))
                y_u = y_u.copy()
                y_u[m] *= noise

        rf_reg = getattr(args,"rf_reg",200)
        rf_days= getattr(args,"rf_days",200)
        rf_cls = getattr(args,"rf_cls",200)
        max_depth=getattr(args,"max_depth",None)

        # ── 학습/평가 분할(그룹 단위)
        if do_eval and len(idx) >= max(10, int(1.0/eval_split)+5):
            Xtr, Xte, ytr_u, yte_u, ytr_d, yte_d, ytr6, yte6, ytr12, yte12, idx_tr, idx_te = \
                _split_many(Xg, y_u, y_d, y_6, y_12, idx, test_size=eval_split, random_state=42)
        else:
            Xtr, Xte = Xg, None
            ytr_u, yte_u = y_u, None
            ytr_d, yte_d = y_d, None
            ytr6, yte6 = y_6, None
            ytr12, yte12 = y_12, None
            idx_tr, idx_te = idx, None

        reg_usage=RandomForestRegressor(n_estimators=rf_reg, max_depth=max_depth, random_state=42, n_jobs=-1).fit(Xtr,ytr_u)
        reg_days =RandomForestRegressor(n_estimators=rf_days,max_depth=max_depth, random_state=42, n_jobs=-1).fit(Xtr,ytr_d)
        cls_6m   =RandomForestClassifier(n_estimators=rf_cls,max_depth=max_depth, random_state=42, n_jobs=-1).fit(Xtr,ytr6)
        cls_12m  =RandomForestClassifier(n_estimators=rf_cls,max_depth=max_depth, random_state=42, n_jobs=-1).fit(Xtr,ytr12)

        models_by_group[(cat,size,man)] = {
            "reg_usage": reg_usage, "reg_days": reg_days, "cls_6m": cls_6m, "cls_12m": cls_12m
        }

        # ── 평가: 예측 MAE(30일 수요) + 발주 MAE
        if do_eval and Xte is not None and len(Xte) > 0:
            pred_usage = reg_usage.predict(Xte)
            y_true_usage_all.extend(list(yte_u))
            y_pred_usage_all.extend(list(pred_usage))

            # 발주 Ground Truth
            if "order_qty_effective" in df_all.columns:
                true_order = df_all.loc[idx_te, "order_qty_effective"].fillna(0).astype(float).values
            else:
                # Fallback: 실제 30일 수요(yte_u)와 opening_stock으로 현실적 발주량 라벨 생성
                used_fallback_for_order = True
                open_stock = df_all.loc[idx_te, "opening_stock"].fillna(0).astype(float).values \
                             if "opening_stock" in df_all.columns else np.zeros_like(yte_u)
                true_order = np.array([
                    _order_from_usage(u30, os_, getattr(args,"service_days",14),
                                      getattr(args,"horizon",30), getattr(args,"pack_size",100))
                    for u30, os_ in zip(yte_u, open_stock)
                ], dtype=float)

            # 예측 발주량: 예측 usage30 + opening_stock 기반
            open_stock_pred = df_all.loc[idx_te, "opening_stock"].fillna(0).astype(float).values \
                              if "opening_stock" in df_all.columns else np.zeros_like(pred_usage)
            pred_order = np.array([
                _order_from_usage(u30, os_, getattr(args,"service_days",14),
                                  getattr(args,"horizon",30), getattr(args,"pack_size",100))
                for u30, os_ in zip(pred_usage, open_stock_pred)
            ], dtype=float)

            y_true_order_all.extend(list(true_order))
            y_pred_order_all.extend(list(pred_order))

    # ── 메타/저장
    meta={
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "train_years": sorted({int(y) for y in df_all["year"].unique()}) if "year" in df_all.columns else [],
        "n_rows": int(len(df_all)),
        "n_parts": int(df_all["part_id"].nunique()),
        "group_count": int(df_all.groupby(["category","size","manufacturer"])["part_id"].nunique().shape[0]),
        "feature_count": len(feature_columns),
        "rf_params": {"rf_reg":getattr(args,"rf_reg",200),"rf_days":getattr(args,"rf_days",200),
                      "rf_cls":getattr(args,"rf_cls",200),"max_depth":getattr(args,"max_depth",None)}
    }

    # ── MAE 출력/기록
    if do_eval and len(y_true_usage_all)>0 and len(y_true_order_all)>0:
        usage_mae = float(mean_absolute_error(y_true_usage_all, y_pred_usage_all))
        order_mae = float(mean_absolute_error(y_true_order_all, y_pred_order_all))
        flag = " (fallback GT)" if used_fallback_for_order and "order_qty_effective" not in df_all.columns else ""
        _print(f"[eval] 예측 MAE (30일 수요): {usage_mae:.3f}")
        _print(f"[eval] 발주 MAE{flag}: {order_mae:.3f}")
        meta["metrics"] = {"usage_mae": usage_mae, "order_mae": order_mae}
    else:
        meta["metrics"] = {}

    bundle={"feature_columns":feature_columns,"models":models_by_group,"meta":meta}
    path=os.path.join(out_dir,"model_bundle.pkl")
    joblib.dump(bundle,path,compress=getattr(args,"compress",3))
    _print(f"[model] 저장: {path}")

    if getattr(args,"save_meta",False):
        with open(os.path.join(out_dir,"model_meta.json"),"w",encoding="utf-8") as f:
            json.dump(meta,f,ensure_ascii=False,indent=2)
        _print("[model] 메타 저장: model_all/model_meta.json")

    return path

def _split_many(Xg, y_u, y_d, y6, y12, idx, test_size=0.2, random_state=42):
    Xtr, Xte, ytr_u, yte_u, idx_tr, idx_te = train_test_split(
        Xg, y_u, idx, test_size=test_size, random_state=random_state
    )
    # 같은 분할을 쓰기 위해 인덱스 기반 매핑
    m_tr = pd.Index(Xtr.index)
    m_te = pd.Index(Xte.index)
    ytr_d = pd.Series(y_d, index=Xg.index).loc[m_tr].values
    yte_d = pd.Series(y_d, index=Xg.index).loc[m_te].values
    ytr6  = pd.Series(y6,  index=Xg.index).loc[m_tr].values
    yte6  = pd.Series(y6,  index=Xg.index).loc[m_te].values
    ytr12 = pd.Series(y12, index=Xg.index).loc[m_tr].values
    yte12 = pd.Series(y12, index=Xg.index).loc[m_te].values
    return Xtr, Xte, ytr_u, yte_u, ytr_d, yte_d, ytr6, yte6, ytr12, yte12, idx_tr, idx_te

# ──────────────────────── 최적화/도우미 ────────────────────────
from dataclasses import dataclass

@dataclass
class PartState:
    part_id:int
    opening_stock:float
    lead_time_days:int=1
    pack_size:int=100
    moq:int=0

def _price_forecast_simple(unit_price:float, horizon:int)->np.ndarray:
    base = float(unit_price) if unit_price>0 else 100.0
    rng=np.random.default_rng(123)
    return base*(1.0 + rng.normal(0,0.002,size=horizon))

def _demand_forecast_from_pred(mu:float, horizon:int)->np.ndarray:
    return np.full(horizon, float(max(mu,0.0)), dtype=float)

def optimize_order_day_quantity(state:PartState, demand:np.ndarray, price:np.ndarray,
                                horizon=30, service_days=14, holding_rate_per_day=0.0005,
                                penalty_mult=5.0):
    H=min(horizon,len(demand),len(price))
    if H<=0: return []
    out=[]
    for d in range(H):
        arr=d+state.lead_time_days
        pre=demand[:min(arr,H)].sum()
        stock_at_arr=state.opening_stock - pre
        unit= float(price[d])
        penalty = max(0.0, -stock_at_arr) * unit * penalty_mult

        need = demand[arr:min(arr+service_days,H)].sum()
        base_q = max(0.0, need - max(0.0, stock_at_arr))
        q = int(max(base_q, state.moq))
        if state.pack_size>0:
            q = int(np.ceil(q/state.pack_size)*state.pack_size)

        purchase = unit*q
        window = demand[arr:min(arr+service_days,H)]
        avg_consumed = window.mean()*len(window) if len(window) else 0.0
        avg_carry = max(0.0, q - avg_consumed)
        holding = holding_rate_per_day * unit * avg_carry * max(1,len(window))
        total = purchase + holding + penalty
        out.append((total,d,q,unit,penalty,holding))
    out.sort(key=lambda x:x[0])
    return [{"day_offset":int(d),"quantity":int(q),"expected_unit_price":round(p,4),
             "expected_total_cost":round(t,2),"stockout_penalty":round(pen,2),
             "holding_cost":round(h,2)} for (t,d,q,p,pen,h) in out[:3]]

# ─────────────────────────── 추론(콘솔 출력) ───────────────────────────
def _build_X_predict(rows:pd.DataFrame, feat_cols:List[str])->pd.DataFrame:
    base=[
        "opening_stock","planned_usage","used_actual","pending_inbound_before_order",
        "lead_time_days","dow","month","rolling7_used","rolling30_used",
        "lag1_used","lag7_used","lag30_used","roll7_std_used","roll30_std_used",
        "unit_price","monthly_discount","shipping_fee","region_fee"
    ]
    for c in base:
        if c not in rows.columns: rows[c]=0.0
    rows2 = rows[base+["category","size","manufacturer"]].copy()
    X = pd.get_dummies(rows2,columns=["category","size","manufacturer"],drop_first=True)
    for col in feat_cols:
        if col not in X.columns: X[col]=0
    X = X[feat_cols]
    return X

def _pick_model(models_by_group:dict, cat:str, size:str, man:str):
    key=(cat,size,man)
    if key in models_by_group: return models_by_group[key]
    for (c,s,m),mdl in models_by_group.items():
        if c==cat and s==size: return mdl
    return next(iter(models_by_group.values()))

def _load_bundle()->dict:
    p=os.path.join(MODEL_DIR,"model_bundle.pkl")
    if not os.path.exists(p): raise FileNotFoundError("model_bundle.pkl 없음. 먼저 --retrain 실행.")
    return joblib.load(p)

def _predict_rows(rows:pd.DataFrame, args)->pd.DataFrame:
    """
    rows: 현재 상태 입력(한 행=한 part).
    필수 컬럼: part_id, category, size, manufacturer, quantity(=opening_stock 원시)
    """
    b=_load_bundle()
    models=b["models"]; feats=b["feature_columns"]

    rows=rows.copy()

    # 그대로 사용(Null만 처리)
    if "category" in rows.columns:
        rows["category"]=rows["category"].map(_norm_category)
    if "size" in rows.columns:
        rows["size"]=rows["size"].map(_norm_size)
    if "manufacturer" in rows.columns:
        rows["manufacturer"]=rows["manufacturer"].map(_norm_manufacturer)

    now=pd.Timestamp("today")
    rows["dow"]=now.dayofweek; rows["month"]=now.month

    # 원시/계산 재고 분리
    rows.rename(columns={"quantity":"opening_stock_raw"}, inplace=True)
    if getattr(args,"allow_negative_in_calc",False):
        rows["opening_stock"]=rows["opening_stock_raw"]
    else:
        rows["opening_stock"]=rows["opening_stock_raw"].clip(lower=0)

    X = _build_X_predict(rows, feats)

    out=[]
    rng=np.random.default_rng(getattr(args,"seed",1234))
    pr=getattr(args,"event_prob",0.08)
    lo,hi=(0.03,0.08)
    if getattr(args,"event_range",None): lo,hi=args.event_range

    horizon=getattr(args,"horizon",30)
    svc_days=getattr(args,"service_days",14)
    hold_rate=getattr(args,"holding_rate_per_day",0.0005)
    pen_mult=getattr(args,"penalty_multiplier",5.0)
    pack_size=getattr(args,"pack_size",100)
    moq=getattr(args,"moq",0)

    for i,r in rows.iterrows():
        cat,size,man = r["category"], str(r["size"]), str(r["manufacturer"])
        mdl=_pick_model(models,cat,size,man)
        Xi=X.iloc[[i]]

        # 수요(미래30일), 소진일, 위험
        usage30 = float(mdl["reg_usage"].predict(Xi)[0])
        days    = float(mdl["reg_days"].predict(Xi)[0])
        risk6   = bool(mdl["cls_6m"].predict(Xi)[0])
        risk12  = bool(mdl["cls_12m"].predict(Xi)[0])

        # 확률 이벤트(8%): ±(3~8%) 편차
        event=False; factor=1.0
        if rng.random()<pr:
            factor = float(rng.uniform(1.0-lo, 1.0+hi))
            usage30 *= factor
            event=True

        # 최적화용 수요/가격 벡터 구성
        mu = max(usage30/horizon, float(r.get("rolling7_used",0.0)))
        demand_vec = _demand_forecast_from_pred(mu, horizon)
        unit_price = float(r.get("unit_price",0.0)) if "unit_price" in r else 100.0
        if unit_price<=0: unit_price=100.0
        price_vec = _price_forecast_simple(unit_price, horizon)

        state=PartState(
            part_id=int(r["part_id"]),
            opening_stock=float(r["opening_stock"]),
            lead_time_days=int(r.get("lead_time_days",1)),
            pack_size=pack_size, moq=moq
        )
        recos = optimize_order_day_quantity(
            state, demand_vec, price_vec, horizon=horizon,
            service_days=svc_days,
            holding_rate_per_day=hold_rate,
            penalty_mult=pen_mult
        )
        out.append({
            "part_id": int(r["part_id"]),
            "category": cat, "size": size, "manufacturer": man,
            "opening_stock_raw": float(r["opening_stock_raw"]),
            "opening_stock_calc": float(r["opening_stock"]),
            "pred_usage_30d": round(usage30,2),
            "pred_days_to_zero": round(days,2),
            "risk_6m": risk6, "risk_12m": risk12,
            "event_applied": event, "event_factor": round(factor,4),
            "recommendations_top3": recos,
            "planned_usage": float(r.get("planned_usage", 0.0)),
            "rolling7_used": float(r.get("rolling7_used", 0.0))
        })
    return pd.DataFrame(out)

# ─────────────────────────── DB/CSV 입력 ───────────────────────────
def _read_from_db()->pd.DataFrame:
    try:
        from db_config import DB_CONFIG
        import pymysql
    except Exception:
        raise RuntimeError("DB 드라이버 또는 설정이 없습니다. --from-csv 를 사용하세요.")

    conn=pymysql.connect(
        host=DB_CONFIG.get('host'), user=DB_CONFIG.get('user'),
        password=DB_CONFIG.get('password'), database=DB_CONFIG.get('database'),
        port=int(DB_CONFIG.get('port',3306)), charset=DB_CONFIG.get('charset','utf8mb4'),
        cursorclass=pymysql.cursors.DictCursor, autocommit=True,
    )
    with conn.cursor() as cur:
        cur.execute("""
            SELECT part_id, part_number, category, size, received_date,
                   is_humidity_sensitive, needs_humidity_control,
                   manufacturer, quantity, min_stock
            FROM pcb_parts
            ORDER BY part_id ASC
        """)
        rows = cur.fetchall() or []
    conn.close()
    df=pd.DataFrame(rows)

    if "category" in df.columns:
        df["category"]=df["category"].map(_norm_category)
    if "size" in df.columns:
        df["size"]=df["size"].map(_norm_size)
    if "manufacturer" in df.columns:
        df["manufacturer"]=df["manufacturer"].map(_norm_manufacturer)
    if "quantity" not in df.columns: df["quantity"]=0
    return df

def _read_from_csv(path:str)->pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    df=pd.read_csv(path)
    if "part_id" not in df.columns or "quantity" not in df.columns:
        raise ValueError("CSV에는 최소 part_id, quantity 컬럼이 있어야 합니다.")
    if "category" in df.columns:
        df["category"]=df["category"].map(_norm_category)
    if "size" in df.columns:
        df["size"]=df["size"].map(_norm_size)
    if "manufacturer" in df.columns:
        df["manufacturer"]=df["manufacturer"].map(_norm_manufacturer)
    return df

# ─────────────────────────── ai-5-3 스타일 요약 출력 ───────────────────────────
def _ai_style_ai_pred_qty(row, horizon:int, service_days:int, pack_size:int)->int:
    """AI 예측 주문량 근사: (30일 수요 * (서비스기간/30)) - 현재 가용재고 → 팩사이즈 올림"""
    need = float(row["pred_usage_30d"]) * (service_days/float(max(horizon,1))) - float(row["opening_stock_calc"])
    if pack_size>0 and need>0:
        return int(np.ceil(need/pack_size)*pack_size)
    return int(max(0.0, need))

def _print_ai53_style_summary(df_pred: pd.DataFrame, args):
    if df_pred is None or df_pred.empty:
        print("\n=== 카테고리별 AI 모델 예측 vs 현실적 계산 비교 ===")
        print("(결과 없음)")
        return

    # (A) 파트별 AI 예측 주문량(근사) 계산 → 카테고리 합
    ai_order_each = df_pred.apply(
        lambda r: _ai_style_ai_pred_qty(r, args.horizon, args.service_days, args.pack_size), axis=1
    )
    df_pred2 = df_pred.copy()
    df_pred2["ai_order_qty"] = ai_order_each

    pred_cat = df_pred2.groupby("category", as_index=False)["ai_order_qty"] \
                       .sum().rename(columns={"ai_order_qty":"ai_predicted_order"})

    # (B) 현재상태 합계(오늘 사용, 재고, rolling7)
    feats_cat = df_pred2.groupby("category", as_index=False).agg(
        total_today_usage=("planned_usage", "sum"),
        total_opening_stock=("opening_stock_calc", "sum"),
        rolling7_used_sum=("rolling7_used", "sum")
    )

    grp = feats_cat.merge(pred_cat, on="category", how="left").fillna({"ai_predicted_order": 0.0})

    # 현실적 주문량 계산
    def _realistic_order_row(r):
        daily_usage_sum = float(r["total_today_usage"]) or 0.0
        rolling7_sum    = float(r["rolling7_used_sum"]) or 0.0
        opening_sum     = float(r["total_opening_stock"]) or 0.0
        denom = daily_usage_sum if daily_usage_sum > 0 else (rolling7_sum if rolling7_sum > 0 else None)
        if denom is None:
            return 0
        need = denom * args.service_days - opening_sum
        if args.pack_size > 0 and need > 0:
            return int(np.ceil(need/args.pack_size) * args.pack_size)
        return int(max(0.0, need))

    grp["realistic_order"] = grp.apply(_realistic_order_row, axis=1)

    # 출력 1: 카테고리별 AI 모델 예측 vs 현실적 계산 비교
    print("\n=== 카테고리별 AI 모델 예측 vs 현실적 계산 비교 ===")
    for _, row in grp.iterrows():
        category = row["category"]
        ai_pred  = float(row["ai_predicted_order"]) or 0.0
        real_ord = float(row["realistic_order"]) or 0.0
        diff     = real_ord - ai_pred
        print(f"{category}:")
        print(f"  - AI 모델 예측: {ai_pred:.0f}개")
        print(f"  - 현실적 계산: {int(real_ord):,}개")
        print(f"  - 차이: {diff:+.0f}개\n")

    # 출력 2: 재고 관리 시나리오 분석(카테고리 합산)
    print("\n=== 재고 관리 시나리오 분석(카테고리 합산) ===")
    for _, row in grp.iterrows():
        category = row["category"]
        daily_usage_sum = float(row["total_today_usage"]) or 0.0
        opening_sum     = float(row["total_opening_stock"]) or 0.0
        rolling7_sum    = float(row["rolling7_used_sum"]) or 0.0

        denom = daily_usage_sum if daily_usage_sum > 0 else (rolling7_sum if rolling7_sum > 0 else None)

        if denom is not None and denom < 1:
            print(f"{category}: N/A (수요가 매우 작음)")
            continue

        if denom is None:
            print(f"{category}: N/A (오늘 사용계획 0, 최근7일 사용량 0)")
            continue

        days_possible = opening_sum / denom if denom > 0 else float('inf')
        print(f"{category}: {days_possible:.1f}일")
        if days_possible < 7:
            recommended_stock = int(daily_usage_sum * 14) if daily_usage_sum > 0 else int(rolling7_sum * 2)
            print(f"  ⚠️  경고: 재고가 7일 미만입니다!")
            print(f"  💡 권장 재고량(카테고리 합산): {recommended_stock:,}개")

# ─────────────────────────── 콘솔용 상세 나열 ───────────────────────────
def _print_grouped_result(df:pd.DataFrame):
    if df is None or df.empty:
        _print("결과가 없습니다.")
        return
    g = df.groupby(["category","size"], as_index=False)
    for (cat, size), chunk in g:
        mans = chunk["manufacturer"].nunique()
        _print(f"\n▶ {cat} / {size}  — 제조사 옵션 {mans}개")
        for _, r in chunk.sort_values(["manufacturer","part_id"]).iterrows():
            pk = r["part_id"]
            stock_raw = r["opening_stock_raw"]
            stock_calc = r["opening_stock_calc"]
            usage30 = r["pred_usage_30d"]
            dleft = r["pred_days_to_zero"]
            eflag = " (이벤트)" if r["event_applied"] else ""
            _print(f"  - [{pk}] {r['manufacturer']}: 재고(원시/계산)={stock_raw}/{stock_calc}, "
                   f"30일수요={usage30}, 소진예상일={dleft}{eflag}")
            for rec in (r["recommendations_top3"] or []):
                _print(f"      · day+{rec['day_offset']}, qty={rec['quantity']}, "
                       f"단가≈{rec['expected_unit_price']}, 총비용≈{rec['expected_total_cost']} "
                       f"(결품페널티≈{rec['stockout_penalty']}, 보유≈{rec['holding_cost']})")

# ─────────────────────────── main/CLI ───────────────────────────
def main():
    ap=argparse.ArgumentParser()
    # 입력원
    ap.add_argument("--years", type=str, default="2023,2024")
    ap.add_argument("--retrain", action="store_true")
    ap.add_argument("--predict", action="store_true")
    ap.add_argument("--from-db", action="store_true")
    ap.add_argument("--from-csv", type=str, default="")
    # 최적화/정책
    ap.add_argument("--horizon", type=int, default=30)
    ap.add_argument("--service-days", type=int, default=14)
    ap.add_argument("--pack-size", type=int, default=100)
    ap.add_argument("--moq", type=int, default=0)
    ap.add_argument("--holding-rate-per-day", type=float, default=0.0005)
    ap.add_argument("--penalty-multiplier", type=float, default=5.0)
    # 확률 이벤트
    ap.add_argument("--event-prob", type=float, default=0.08)
    ap.add_argument("--event-range", nargs=2, type=float, default=None, metavar=("LOW","HIGH"))
    # 음수 재고 계산 정책
    ap.add_argument("--allow-negative-in-calc", action="store_true")
    # 모델 크기/성능
    ap.add_argument("--rf-reg", type=int, default=200)
    ap.add_argument("--rf-days", type=int, default=200)
    ap.add_argument("--rf-cls", type=int, default=200)
    ap.add_argument("--max-depth", type=int, default=None)
    ap.add_argument("--float32", action="store_true")
    ap.add_argument("--compress", type=int, default=3)
    ap.add_argument("--sample-rate", type=float, default=1.0)
    # 메타/시드
    ap.add_argument("--save-meta", action="store_true")
    ap.add_argument("--seed", type=int, default=1234)
    # ★ 평가 옵션
    ap.add_argument("--eval-mae", action="store_true", help="훈련 중 홀드아웃으로 예측/발주 MAE 출력")
    ap.add_argument("--eval-split", type=float, default=0.2, help="홀드아웃 비율 (기본 0.2)")

    args=ap.parse_args()
    years=[int(x.strip()) for x in args.years.split(",") if x.strip()]

    # ── 학습
    model_path=os.path.join(MODEL_DIR,"model_bundle.pkl")
    if args.retrain or not os.path.exists(model_path):
        df_all = load_annual_category_data("data", years=years)
        if 0.0 < getattr(args, "sample_rate", 1.0) < 1.0:
            frac = max(0.0, min(1.0, args.sample_rate))
            df_all = df_all.sample(frac=frac, random_state=42).reset_index(drop=True)
        train_and_save_models(df_all, out_dir=MODEL_DIR, args=args)
    else:
        _print(f"[model] Using existing model bundle: {model_path}")

    # ── 추론(옵션)
    if args.predict:
        if args.from_db:
            rows = _read_from_db()
        elif args.from_csv:
            rows = _read_from_csv(args.from_csv)
        else:
            _print("입력원 미지정: --from-db 또는 --from-csv <path> 지정 필요.")
            return
        df = _predict_rows(rows, args)

        # (A) 상세 나열
        _print_grouped_result(df)
        # (B) ai-5-3 스타일 요약 블록
        _print_ai53_style_summary(df, args)

if __name__ == "__main__":
    main()
