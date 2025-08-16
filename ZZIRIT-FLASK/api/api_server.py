
# api/api_server.py
# Flask Blueprint exposing:
#  - POST /api/predict   : run predictions using ML_model/model_bundle.pkl + current DB
#  - GET  /api/model/meta: model availability & metadata
#
# Requirements:
#   - db_config.py providing DB_CONFIG dict
#   - ML_model/model_bundle.pkl created by ai-5-4.py (--retrain)
#   - pip install flask flask-cors pymysql pandas numpy joblib

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import joblib
import pymysql
from flask import Blueprint, jsonify, request
from pathlib import Path

_HERE = Path(__file__).resolve()
# ZZIRIT-FLASK 디렉토리
_FLASK_ROOT = _HERE.parent.parent
# ────────────────────────────────────────────────────────────────────────────────
# Config
_env_path = os.environ.get("ZZIRIT_MODEL_PATH")

if _env_path:
    MODEL_PATH = Path(_env_path).expanduser().resolve()
else:
    # 2순위: ZZIRIT-FLASK/ML_model/model_bundle.pkl (권장 기본)
    MODEL_PATH = (_FLASK_ROOT / "ML_model" / "model_bundle.pkl").resolve()

MODEL_DIR = str(MODEL_PATH.parent)
MODEL_PATH = str(MODEL_PATH)  # joblib.load가 str/Path 모두 처리 가능하나, 로그 가독성 위해 str로

# db_config.py 에서 DB_CONFIG 로드 (존재하지 않으면 예외 발생)
try:
    from db_config import DB_CONFIG  # type: ignore
except Exception as e:  # pragma: no cover
    DB_CONFIG = None  # 런타임에서 오류로 응답
    logging.warning("db_config.DB_CONFIG 로드를 실패했습니다: %s", e)

# Flask Blueprint (app.py에서 url_prefix='/api' 로 등록됨)
api_bp = Blueprint("api_server", __name__)

# 전역 모델 캐시
_MODEL_BUNDLE: Dict[str, Any] | None = None


def _load_model_bundle() -> Dict[str, Any]:
    """사전 학습된 모델 번들(model_bundle.pkl)을 1회 로드/캐싱"""
    global _MODEL_BUNDLE
    if _MODEL_BUNDLE is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"모델 파일이 없습니다: {MODEL_PATH}. 먼저 ai-5-4.py --retrain 을 실행하세요.")
        _MODEL_BUNDLE = joblib.load(MODEL_PATH)
        logging.info("✅ model_bundle 로드 완료: %s", MODEL_PATH)
    return _MODEL_BUNDLE


def _get_db_conn():
    """PyMySQL 연결 (DictCursor)"""
    if not DB_CONFIG:
        raise RuntimeError("DB 설정(DB_CONFIG)이 없습니다. db_config.py를 확인하세요.")
    conn = pymysql.connect(
        host=DB_CONFIG.get("host"),
        user=DB_CONFIG.get("user"),
        password=DB_CONFIG.get("password"),
        database=DB_CONFIG.get("database"),
        port=int(DB_CONFIG.get("port", 3306)),
        charset=DB_CONFIG.get("charset", "utf8mb4"),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )
    return conn


# ────────────────────────────────────────────────────────────────────────────────
# Normalizers (ai-5-4.py와 동작 일치)
# ────────────────────────────────────────────────────────────────────────────────
def _norm_category(x: Any) -> str:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return "Unknown"
    return str(x).strip()


def _norm_size(s: Any) -> str:
    if s is None:
        return "Unknown"
    txt = str(s).strip()
    if "/" in txt:
        txt = txt.split("/")[0].strip()
    # "402" -> "0402" 패딩
    digits = "".join([c for c in txt if c.isdigit()])
    if digits.isdigit():
        return digits.zfill(4) if len(digits) == 3 else digits
    return txt


def _norm_manufacturer(x: Any) -> str:
    if x is None:
        return "unknown"
    return str(x).strip()


# ────────────────────────────────────────────────────────────────────────────────
# Mini Optimizer (ai-5-4.py의 아이디어 기반 경량 구현)
# ────────────────────────────────────────────────────────────────────────────────
class PartState:
    def __init__(self, part_id: int, opening_stock: float, lead_time_days: int, pack_size: int, moq: int):
        self.part_id = part_id
        self.opening_stock = float(opening_stock)
        self.lead_time_days = int(lead_time_days)
        self.pack_size = int(pack_size)
        self.moq = int(moq)


def _price_forecast(unit_price: float | None, horizon: int) -> np.ndarray:
    base = float(unit_price) if (unit_price is not None and unit_price > 0) else 100.0
    rng = np.random.default_rng(123)
    return base * (1.0 + rng.normal(0, 0.002, size=horizon))


def _demand_from_usage30(usage30: float, horizon: int) -> np.ndarray:
    mu = max(usage30 / max(horizon, 1), 0.0)
    return np.full(horizon, mu, dtype=float)


def _optimize(state: PartState, demand: np.ndarray, price: np.ndarray,
              horizon: int, service_days: int, hold_rate_per_day: float, penalty_mult: float) -> List[Dict[str, Any]]:
    H = min(horizon, len(demand), len(price))
    if H <= 0:
        return []
    outcomes: List[tuple] = []
    for d in range(H):
        arrival_day = d + state.lead_time_days
        consumed_before_arrival = float(demand[:min(arrival_day, H)].sum())
        stock_at_arrival = state.opening_stock - consumed_before_arrival
        unit_price = float(price[d])

        penalty_cost = max(0.0, -stock_at_arrival) * unit_price * penalty_mult

        window = demand[arrival_day:min(arrival_day + service_days, H)]
        need_qty = float(window.sum())
        base_order = max(0.0, need_qty - max(0.0, stock_at_arrival))
        order_qty = int(max(base_order, state.moq))
        if state.pack_size > 0:
            order_qty = int(np.ceil(order_qty / state.pack_size) * state.pack_size)

        purchase_cost = unit_price * order_qty
        avg_carry = max(0.0, order_qty - float(window.mean() * len(window) if len(window) else 0.0))
        holding_cost = hold_rate_per_day * unit_price * avg_carry * max(1, len(window))
        total_cost = purchase_cost + holding_cost + penalty_cost
        outcomes.append((total_cost, d, order_qty, unit_price, penalty_cost, holding_cost))

    outcomes.sort(key=lambda x: x[0])
    top3 = []
    for (total, d, qty, unit, pen, hold) in outcomes[:3]:
        top3.append({
            "day_offset": int(d),
            "quantity": int(qty),
            "expected_total_cost": round(float(total), 2),
            # 추가 정보(프론트 타입에 없지만 있어도 무해)
            "expected_unit_price": round(float(unit), 4),
            "stockout_penalty": round(float(pen), 2),
            "holding_cost": round(float(hold), 2),
        })
    return top3


# ────────────────────────────────────────────────────────────────────────────────
# Routes
# ────────────────────────────────────────────────────────────────────────────────
@api_bp.route("/model/meta", methods=["GET"])
def model_meta():
    """모델 파일 존재 및 로드 가능 여부"""
    available = os.path.exists(MODEL_PATH)
    meta = None
    try:
        if available:
            b = _load_model_bundle()
            meta = b.get("meta")
    except Exception as e:
        logging.warning("model_meta: 로드 중 문제: %s", e)
        available = False
        meta = None
    return jsonify({"available": available, "path": MODEL_PATH, "meta": meta})


@api_bp.route("/predict", methods=["POST"])
def predict():
    """
    요청 JSON 예:
    {
      "years":[2022,2023,2024],
      "service_days":14,
      "pack_size":100,
      "moq":0,
      "holding_rate_per_day":0.0005,
      "penalty_multiplier":5.0
    }
    """
    params = request.get_json(silent=True) or {}
    service_days = int(params.get("service_days", 14))
    pack_size = int(params.get("pack_size", 100))
    moq = int(params.get("moq", 0))
    hold_rate = float(params.get("holding_rate_per_day", 0.0005))
    pen_mult = float(params.get("penalty_multiplier", 5.0))

    try:
        bundle = _load_model_bundle()
        models: Dict[tuple, Dict[str, Any]] = bundle["models"]
        feat_cols: List[str] = bundle["feature_columns"]
    except Exception as e:
        logging.error("모델 로드 실패: %s", e, exc_info=True)
        return jsonify({"error": "Model not available", "message": str(e)}), 500

    # DB 로드
    try:
        conn = _get_db_conn()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT part_id, part_number, category, size, received_date,
                       is_humidity_sensitive, needs_humidity_control,
                       manufacturer, quantity, min_stock
                FROM pcb_parts
                ORDER BY part_id ASC
                """
            )
            rows = cur.fetchall() or []
    except Exception as e:
        logging.error("DB 조회 실패: %s", e, exc_info=True)
        return jsonify({"error": "Database query failed", "message": str(e)}), 500
    finally:
        try:
            conn.close()
        except Exception:
            pass

    if not rows:
        return jsonify({"generated_at": pd.Timestamp.now().isoformat(), "n_parts": 0, "items": [], "summary": {}})

    df = pd.DataFrame(rows)
    # 정규화
    df["category"] = df.get("category", "").map(_norm_category)
    df["size"] = df.get("size", "").map(_norm_size)
    df["manufacturer"] = df.get("manufacturer", "").map(_norm_manufacturer)
    now = pd.Timestamp.now()
    df["dow"] = now.dayofweek
    df["month"] = now.month
    df["opening_stock_raw"] = df.get("quantity", 0)
    df["opening_stock"] = df["opening_stock_raw"].clip(lower=0)

    # 기본 피처 채우기
    base_cols = [
        "opening_stock", "planned_usage", "used_actual", "pending_inbound_before_order",
        "lead_time_days", "dow", "month", "rolling7_used", "rolling30_used",
        "lag1_used", "lag7_used", "lag30_used", "roll7_std_used", "roll30_std_used",
        "unit_price", "monthly_discount", "shipping_fee", "region_fee"
    ]
    for col in base_cols:
        if col not in df.columns:
            df[col] = 0.0
    if "lead_time_days" not in df.columns:
        df["lead_time_days"] = 1

    # 더미 인코딩 → 학습 피처 정렬
    X = pd.get_dummies(df[base_cols + ["category", "size", "manufacturer"]],
                       columns=["category", "size", "manufacturer"], drop_first=True)
    for col in feat_cols:
        if col not in X.columns:
            X[col] = 0
    X = X[feat_cols]

    items: List[Dict[str, Any]] = []

    # 보조: 키 매칭 (정확키 → (cat,size) → 임의 하나)
    def pick_group(cat: str, size: str, man: str) -> Dict[str, Any]:
        key = (cat, size, man)
        if key in models:
            return models[key]
        for (c, s, m), grp in models.items():
            if c == cat and s == size:
                return grp
        # fallback
        return next(iter(models.values()))

    H = 30
    for i, row in df.iterrows():
        cat = row["category"]; size = str(row["size"]); manu = str(row["manufacturer"])
        model_group = pick_group(cat, size, manu)

        Xi = X.iloc[[i]]
        try:
            usage30 = float(model_group["reg_usage"].predict(Xi)[0])
        except Exception:
            usage30 = 0.0
        try:
            days_to_zero = float(model_group["reg_days"].predict(Xi)[0])
        except Exception:
            days_to_zero = 9999.0

        # 위험도(사용할 경우)
        try:
            risk6 = bool(model_group["cls_6m"].predict(Xi)[0])
            risk12 = bool(model_group["cls_12m"].predict(Xi)[0])
        except Exception:
            risk6 = risk12 = False

        demand_vec = _demand_from_usage30(usage30, H)
        price_vec = _price_forecast(float(row.get("unit_price", 100.0)), H)

        state = PartState(
            part_id=int(row.get("part_id", 0)),
            opening_stock=float(row.get("opening_stock", 0.0)),
            lead_time_days=int(row.get("lead_time_days", 1)),
            pack_size=pack_size,
            moq=moq,
        )
        recos = _optimize(state, demand_vec, price_vec, horizon=H,
                          service_days=service_days, hold_rate_per_day=hold_rate, penalty_mult=pen_mult)

        # 시뮬레이션 기반 best_day_top3 (가벼운 N으로)
        day_counts: Dict[int, int] = {}
        N_sim = 40
        rng = np.random.default_rng(7)
        for _ in range(N_sim):
            usage_sim = usage30
            if rng.random() < 0.08:  # 이벤트 확률 8%
                usage_sim *= rng.uniform(0.97, 1.08)
            demand_sim = _demand_from_usage30(usage_sim, H)
            recos_sim = _optimize(state, demand_sim, price_vec, horizon=H,
                                  service_days=service_days, hold_rate_per_day=hold_rate, penalty_mult=pen_mult)
            if recos_sim:
                best_d = int(recos_sim[0]["day_offset"])
                day_counts[best_d] = day_counts.get(best_d, 0) + 1
        best_day_top3 = [
            {"day_offset": int(d), "prob": round(cnt / max(N_sim, 1), 2)}
            for d, cnt in sorted(day_counts.items(), key=lambda kv: kv[1], reverse=True)[:3]
        ]

        predicted_qty = int(recos[0]["quantity"]) if recos else 0
        best_order_day = int(recos[0]["day_offset"]) if recos else None

        warn_flag = False
        try:
            if row.get("min_stock") is not None and float(row["opening_stock"]) <= float(row["min_stock"]):
                warn_flag = True
        except Exception:
            pass
        if days_to_zero <= service_days:
            warn_flag = True
        # 필요시 risk6/12도 경고에 반영 가능

        items.append({
            "part_id": int(row.get("part_id", 0)),
            "category": cat,
            "size": size,
            "manufacturer": manu,
            "today_usage": 0.0,  # 실시간 데이터 없으므로 0
            "opening_stock": int(row.get("quantity", 0) or 0),
            "predicted_order_qty": predicted_qty,
            "predicted_days_to_depletion": round(float(days_to_zero), 2),
            "warning": bool(warn_flag),
            "recommendations_top3": recos,
            "predicted_best_order_day": best_order_day if best_order_day is not None else None,
            "best_day_top3": best_day_top3,
        })

    # summary.categories: {category, days_possible}
    summary = {"categories": []}
    if items:
        df_items = pd.DataFrame(items)
        for cat, g in df_items.groupby("category"):
            total_usage = float(g["today_usage"].sum() or 0.0)
            total_stock = float(g["opening_stock"].sum() or 0.0)
            if total_usage >= 1.0:
                days_possible = round(total_stock / total_usage, 1)
            else:
                days_possible = None
            summary["categories"].append({"category": cat, "days_possible": days_possible})

    resp = {
        "generated_at": pd.Timestamp.now().isoformat(),
        "n_parts": len(items),
        "items": items,
        "summary": summary,
    }
    return jsonify(resp)
