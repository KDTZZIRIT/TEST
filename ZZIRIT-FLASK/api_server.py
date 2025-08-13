import os, json, time
from typing import Any, Dict, List
from flask import Flask, request, jsonify
import joblib
import numpy as np
import pandas as pd
from flask import Blueprint

ai_bp = Blueprint('ai', __name__, url_prefix='/api/ai')

@ai_bp.route('/predict', methods=['POST'])
def predict():
    # 기존 predict 함수 내용
    pass

# app.py에서 등록
app.register_blueprint(ai_bp)
# === 전역(싱글톤) ===
app = Flask(__name__)
_BUNDLE = None
_META = None
_LAST_META_TS = 0.0

MODEL_DIR = os.environ.get("MODEL_DIR", "/app/model_all")
BUNDLE_PATH = os.path.join(MODEL_DIR, "model_bundle.pkl")

# ---- 워밍업: 기동 시 모델 메모리맵으로 로드 ----
def _load_bundle():
    global _BUNDLE, _META, _LAST_META_TS
    if _BUNDLE is None:
        t0 = time.time()
        _BUNDLE = joblib.load(BUNDLE_PATH, mmap_mode="r")  # 메모리 맵
        _META = _BUNDLE.get("meta", {})
        _LAST_META_TS = time.time()
        print(f"[model] loaded in {time.time()-t0:.2f}s, features={len(_BUNDLE.get('feature_columns', []))}")
    return _BUNDLE

@app.get("/health")
def health():
    ok = os.path.exists(BUNDLE_PATH)
    return jsonify({"ok": ok})

@app.get("/api/model/meta")
def model_meta():
    try:
        _load_bundle()
        # 3초 캐시
        global _LAST_META_TS
        if time.time() - _LAST_META_TS > 3:
            _LAST_META_TS = time.time()
        return jsonify({"available": True, "meta": _META, "updated_at": _META.get("created_at")})
    except Exception as e:
        return jsonify({"available": False, "error": str(e)}), 500

# === 예측 ===
def _predict_core(rows: pd.DataFrame, args: Dict[str, Any]) -> Dict[str, Any]:
    from ai-5-4 import _build_X_predict, _pick_model, _demand_forecast_from_pred, _price_forecast_simple, optimize_order_day_quantity

    b = _load_bundle()
    models = b["models"]
    feats  = b["feature_columns"]

    # 입력 정규화(필수 컬럼)
    for c in ["part_id","category","size","manufacturer","quantity"]:
        if c not in rows.columns: rows[c] = None
    now = pd.Timestamp("today")
    rows["dow"] = now.dayofweek
    rows["month"] = now.month
    rows = rows.rename(columns={"quantity": "opening_stock"})
    rows["opening_stock"] = rows["opening_stock"].clip(lower=0)

    X = _build_X_predict(rows, feats)

    horizon  = int(args.get("horizon", 30))
    svc      = int(args.get("service_days", 14))
    hold     = float(args.get("holding_rate_per_day", 0.0005))
    pen_mult = float(args.get("penalty_multiplier", 5.0))
    pack     = int(args.get("pack_size", 100))
    moq      = int(args.get("moq", 0))

    items: List[Dict[str, Any]] = []
    for i, r in rows.iterrows():
        cat, size, man = r["category"], str(r["size"]), str(r["manufacturer"])
        mdl = _pick_model(models, cat, size, man)
        Xi  = X.iloc[[i]]

        # 30일 사용량 / 소진일
        usage30 = float(mdl["reg_usage"].predict(Xi)[0])
        days    = float(mdl["reg_days"].predict(Xi)[0])

        # 단가(없으면 100)
        unit_price = float(r.get("unit_price", 0.0) or 100.0)
        demand_vec = _demand_forecast_from_pred(max(usage30/horizon, 0.0), horizon)
        price_vec  = _price_forecast_simple(unit_price, horizon)

        from ai-5-4 import PartState
        state = PartState(int(r["part_id"]), float(r["opening_stock"]), int(r.get("lead_time_days", 1)), pack, moq)
        recos = optimize_order_day_quantity(state, demand_vec, price_vec, horizon=horizon,
                                            service_days=svc, holding_rate_per_day=hold, penalty_mult=pen_mult)

        # 프론트 호환 필드(최소)
        best = recos[0] if recos else None
        items.append({
            "part_id": int(r["part_id"]),
            "category": cat, "size": size, "manufacturer": man,
            "today_usage": int(r.get("used_actual", 0) or 0),
            "opening_stock": int(r.get("opening_stock", 0) or 0),
            "predicted_order_qty": int(best["quantity"]) if best else 0,
            "predicted_days_to_depletion": round(days, 2),
            "warning": bool(days <= 7),
            "recommendations_top3": recos,
            # (옵션) UI 배지용 근사 확률
            "best_day_top3": [{"day_offset": (best or {"day_offset": 0})["day_offset"], "prob": 0.65}] if best else []
        })

    # 카테고리별 커버 일수 요약(간단 추정)
    df = pd.DataFrame(items)
    cats = []
    if not df.empty:
        for c, g in df.groupby("category"):
            d = float(np.nanmean(g["predicted_days_to_depletion"])) if len(g) else None
            cats.append({"category": c, "days_possible": None if d is None else round(d,1)})

    out = {
        "generated_at": pd.Timestamp.utcnow().isoformat(),
        "n_parts": len(items),
        "items": items,
        "summary": {"categories": cats}
    }
    return out

@app.post("/api/predict")
def predict():
    """
    옵션 쿼리:
      ?limit=500&warningOnly=0
    바디(JSON):
      { years: [2023,2024], service_days, pack_size, ... }
    """
    try:
      args = request.get_json(force=True, silent=True) or {}
    except Exception:
      args = {}

    # 입력 파트는 DB/CSV에서 가져오되, 여기서는 경량 더미 or DB 호출로 전환 가능
    # 실제 운영: DB에서 현재 재고/메타 조회 → rows 구성
    # 아래는 예시 rows (필요 시 Node에서 넘겨 받은 파라미터로 대체도 가능)
    limit = int(request.args.get("limit", "600"))
    warning_only = request.args.get("warningOnly", "0") == "1"

    # === 예시: DB에서 가져오도록 수정 가능 ===
    # from db_handler import query_db
    # rows_db = query_db("SELECT part_id, category, size, manufacturer, quantity FROM pcb_parts ORDER BY part_id LIMIT %s", (limit,))
    # rows = pd.DataFrame(rows_db)

    # 임시(데모): 빈 데이터면 100개 더미
    rows = pd.DataFrame([{
        "part_id": i+1, "category": "Capacitor" if i%2==0 else "Resistor",
        "size": "0402", "manufacturer": "samsung" if i%3==0 else "murata",
        "quantity": (i%30)*100 + 2000, "used_actual": (i%7)*5
    } for i in range(limit)])

    result = _predict_core(rows, args)

    if warning_only:
        items = [x for x in result["items"] if x.get("warning")]
        result["items"] = items
        result["n_parts"] = len(items)

    # 응답 최소화(+ gzip 권장)
    return jsonify(result), 200
