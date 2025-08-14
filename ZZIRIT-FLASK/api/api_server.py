# api_server.py
import os
import json
import joblib
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import importlib.util
from pathlib import Path

# 추가: DB 연결
try:
    from db_config import DB_CONFIG
    import pymysql
except Exception:
    DB_CONFIG = None
    pymysql = None

ROOT = Path(__file__).resolve().parent
MODEL_DIR = ROOT / "ML_model"
DATA_DIR = ROOT / "data"
PKL_PATH = MODEL_DIR / "model_bundle.pkl"
META_PATH = MODEL_DIR / "model_meta.json"
# api_server.py 전역
_BUNDLE = None
_BUNDLE_MTIME = None

# DB 유틸
def _get_db_conn():
    if DB_CONFIG is None or pymysql is None:
        return None
    try:
        return pymysql.connect(
            host=DB_CONFIG.get('host'),
            user=DB_CONFIG.get('user'),
            password=DB_CONFIG.get('password'),
            database=DB_CONFIG.get('database'),
            port=int(DB_CONFIG.get('port', 3306)),
            charset=DB_CONFIG.get('charset', 'utf8mb4'),
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True,
        )
    except Exception as e:
        print(f"[db] connection failed: {e}")
        return None

def _load_bundle():
    global _BUNDLE, _BUNDLE_MTIME
    p = PKL_PATH
    if not p.exists(): return None
    mtime = p.stat().st_mtime
    if _BUNDLE is None or _BUNDLE_MTIME != mtime:
        _BUNDLE = joblib.load(p)
        _BUNDLE_MTIME = mtime
    return _BUNDLE

# --- ai-5-3.py 모듈 동적 로드 ---
def _load_ai_module():
    ai_path = ROOT / "ai-5-3.py"   # ★ 경로 다르면 수정
    spec = importlib.util.spec_from_file_location("ai5", str(ai_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore
    return mod

ai5 = _load_ai_module()

app = Flask(__name__)
CORS(app)

# ============ 유틸 ============
def _safe_int(v, default=0):
    try:
        return int(v)
    except:
        return default

def _default_args(payload: dict):
    return {
        "years": payload.get("years", [2022]),
        "service_days": _safe_int(payload.get("service_days", 14)),
        "pack_size": _safe_int(payload.get("pack_size", 100)),
        "moq": _safe_int(payload.get("moq", 0)),
        "holding_rate_per_day": float(payload.get("holding_rate_per_day", 0.0005)),
        "penalty_multiplier": float(payload.get("penalty_multiplier", 5.0)),
        "board_plan": payload.get("board_plan") or {},  # {"PCB-A101": 12, ...}
    }
# _default_args 바로 아래에 유틸 추가
def _norm_years(val):
    if isinstance(val, str):
        return [int(x) for x in val.split(",") if x.strip().isdigit()]
    if isinstance(val, (list, tuple)):
        return [int(x) for x in val]
    return [2022]


def _load_meta():
    if META_PATH.exists():
        with open(META_PATH, encoding="utf-8") as f:
            return json.load(f)
    # pkl에서 meta 재구성(없을 수도 있음)
    b = _load_bundle()
    return (b or {}).get("meta", {})

# ============ API ============
@app.get("/api/model/meta")
def model_meta():
    meta = _load_meta() or {}
    return jsonify({
        "available": bool(_load_bundle()),
        "meta": meta,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    })
@app.get("/api/health")
def health():
    return jsonify({"ok": True, "model": bool(_load_bundle())})

# 사용자 인벤토리: DB에서 직접 조회
@app.get("/api/user/pcb-parts")
def list_pcb_parts():
    conn = _get_db_conn()
    if conn is None:
        return jsonify({"error": "db unavailable"}), 500
    try:
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
            # 프론트가 기대하는 키명 변환(일부 필드 병행 표기)
            out = []
            for r in rows:
                out.append({
                    "id": r.get("part_id"),
                    "part_id": r.get("part_id"),
                    "partId": r.get("part_id"),
                    "part_number": r.get("part_number"),
                    "product": r.get("part_number"),
                    "category": r.get("category"),
                    "type": r.get("category"),
                    "size": r.get("size"),
                    "received_date": r.get("received_date"),
                    "is_humidity_sensitive": r.get("is_humidity_sensitive"),
                    "needs_humidity_control": r.get("needs_humidity_control"),
                    "manufacturer": r.get("manufacturer"),
                    "quantity": r.get("quantity") or 0,
                    "min_stock": r.get("min_stock") or 0,
                    "minimumStock": r.get("min_stock") or 0,
                })
            return jsonify(out)
    except Exception as e:
        return jsonify({"error": f"db query failed: {e}"}), 500
    finally:
        try:
            conn.close()
        except Exception:
            pass

# 임시: 결함 데이터 엔드포인트(없는 경우 404 방지)
@app.get("/api/user/pcb-defect")
def list_pcb_defect():
    return jsonify([])

@app.post("/api/predict")
def predict():
    """
    요청 스키마(예):
    {
      "years": [2022,2023,2024],
      "board_plan": {"PCB-A101": 12, ...},   // 선택
      "service_days": 14,
      "pack_size": 100,
      "moq": 0,
      "holding_rate_per_day": 0.0005,
      "penalty_multiplier": 5.0
    }
    """
    payload = request.get_json(silent=True) or {}
    args = _default_args(payload)
    args["years"] = _norm_years(args["years"])

    bundle = _load_bundle()
    if not bundle:
        return jsonify({"error": "model_bundle.pkl not found"}), 404

    # 1) 예측용 데이터 로드 (★ ai-5-3의 함수명과 일치해야 함)
    try:
        df_all = ai5.load_annual_category_data(str(DATA_DIR), args["years"])  # ★
    except Exception as e:
        return jsonify({"error": f"data load failed: {e}"}), 500

    # 2) 오늘 계획 병합 (board_plan → pid 사용량 변환)
    try:
        board_plan = args["board_plan"] or {}
        # (A) 키가 'PCB-'로 시작하면 PCB 계획으로 판단 → part_id 사용량 맵으로 변환
        if board_plan and all(isinstance(k, str) and k.startswith("PCB-") for k in board_plan.keys()):
            # ai-5-3.py 안의 보드-부품 매핑 함수/상수 가져오기
            get_board_map = getattr(ai5, "load_fixed_board_parts_map", None)
            board_map = get_board_map() if callable(get_board_map) else getattr(ai5, "BOARD_PARTS_MAP")
            today_usage_by_pid = {}
            for b, cnt in board_plan.items():
                if b not in board_map:
                    continue
                for pid, per_board in board_map[b].items():
                    today_usage_by_pid[int(pid)] = today_usage_by_pid.get(int(pid), 0) + int(per_board) * int(cnt)
        else:
            # (B) 이미 pid→수량 맵이면 그대로 사용
            today_usage_by_pid = {int(k): int(v) for k, v in board_plan.items()}

        feats_today = ai5.merge_today_plan_with_inventory(df_all, today_usage_by_pid)
    except Exception as e:
        return jsonify({"error": f"merge plan failed: {e}"}), 500


    # 3) 모델 추론
    try:
        preds = ai5.predict_today(PKL_PATH, feats_today)  # ★ reg_order, reg_days, cls_* 사용
    except Exception as e:
        return jsonify({"error": f"inference failed: {e}"}), 500

    # 4) Top-3 추천 계산 (ai-5-3의 동일 로직 사용)
    try:
        recs = []
        pack = args["pack_size"]
        moq = args["moq"]
        hrate = args["holding_rate_per_day"]
        pmult = args["penalty_multiplier"]
        horizon = 30

        # part별 히스토리 캐시
        by_pid_hist = {
            int(pid): df_all[df_all["part_id"] == int(pid)].copy()
            for pid in feats_today["part_id"].unique()
        }

        # 필요한 함수/클래스 alias
        PartState = getattr(ai5, "PartState")
        price_fc  = getattr(ai5, "_price_forecast_from_history")
        dem_fc    = getattr(ai5, "_demand_forecast_from_today_row")
        optimize  = getattr(ai5, "optimize_order_day_quantity")

        for r in preds:
            pid = int(r["part_id"])
            row = feats_today[feats_today["part_id"] == pid].iloc[0]

            # 가격/수요 벡터 생성
            price_vec  = price_fc(by_pid_hist[pid], pid, horizon)
            demand_vec = dem_fc(row, horizon)

            # 상태 객체 구성
            state = PartState(
                part_id=pid,
                opening_stock=float(r["opening_stock"]),
                lead_time_days=int(row.get("lead_time_days", 1)),
                pack_size=pack,
                moq=moq
            )

            # 최적화 결과(Top-3)
            recos = optimize(
                state, demand_vec, price_vec, horizon=horizon,
                service_days=args["service_days"], holding_rate_per_day=hrate,
                stockout_penalty_multiplier=pmult
            )
            r["recommendations_top3"] = recos
            recs.append(r)
    except Exception as e:
        return jsonify({"error": f"top3 calc failed: {e}"}), 500


    # 5) 카테고리 요약(일수/경고) — 콘솔 출력과 유사
    summary = {}
    try:
        import numpy as np
        g = feats_today.groupby("category", as_index=False).agg(
            total_today_usage=("planned_usage", "sum"),
            total_opening_stock=("opening_stock", "sum"),
            rolling7_used_sum=("rolling7_used", "sum")
        )
        cats = []
        for _, row in g.iterrows():
            cat = str(row["category"])
            du = float(row["total_today_usage"]) or 0.0
            os_ = float(row["total_opening_stock"]) or 0.0
            r7 = float(row["rolling7_used_sum"]) or 0.0
            denom = du if du > 0 else (r7 if r7 > 0 else None)
            if denom is None or denom < 1:
                cats.append({"category": cat, "days_possible": None})
            else:
                cats.append({"category": cat, "days_possible": round(os_ / denom, 2)})
        summary = {"categories": cats}
    except Exception:
        summary = {}

    return jsonify({
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "n_parts": len(recs),
        "items": recs,
        "summary": summary
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
