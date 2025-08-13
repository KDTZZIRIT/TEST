# data.py  (v3 – SMT 비중 고정, k단위 스타트 재고, 월별 대량발주 할인)
# ============================================================
# 목적:
#  - DB에서 부품 메타(part_id, category, size, manufacturer)만 읽어와
#  - 3년(기본 2022~2024) 더미 시계열을 생성 (Part_<pid>.csv)
#  - SMT "비중(weight) 모드"로 보드/BOM 없이도 일일 사용량을 146개 부품에 분배
#  - 스타트 재고는 k(1000ea) 단위의 가중 랜덤
#  - 리드타임=1, 팩사이즈=100, MOQ=0 고정
#  - 월별 제조사(삼성/무라타) 랜덤 대량발주 추가 할인(-3~5%)
#  - 발주량 불일치(과다·과소) 이벤트 확률 8%
# ============================================================

import os, shutil, argparse
from typing import Dict, List
import numpy as np
import pandas as pd
from collections import deque, defaultdict

# --- DB 접근 (db_handler.query_db 우선, 실패 시 db_config+pymysql 폴백) ---
def _get_query_db():
    try:
        from db_handler import query_db
        return query_db
    except Exception:
        import pymysql
        try:
            from db_config import DB_CONFIG as _DB
        except Exception:
            _DB = {
                "host": os.getenv("DB_HOST", "127.0.0.1"),
                "user": os.getenv("DB_USER", "root"),
                "password": os.getenv("DB_PASSWORD", ""),
                "database": os.getenv("DB_NAME", ""),
                "port": int(os.getenv("DB_PORT", "3306")),
                "charset": os.getenv("DB_CHARSET", "utf8mb4"),
            }
        def _q(sql: str, params: tuple | None = None):
            conn = pymysql.connect(
                host=_DB["host"], user=_DB["user"], password=_DB["password"],
                database=_DB["database"], port=int(_DB["port"]),
                charset=_DB["charset"], cursorclass=pymysql.cursors.DictCursor, autocommit=True
            )
            try:
                with conn.cursor() as cur:
                    cur.execute(sql, params or ())
                    return cur.fetchall()
            finally:
                conn.close()
        return _q

query_db = _get_query_db()

# ----------------------- 파라미터(기본값) -----------------------
DEFAULT_YEARS = [2022, 2023, 2024]
LEAD_TIME_DAYS = 1      # 리드타임
PACK_SIZE = 100         # 팩사이즈
MOQ = 0                 # 최소주문수량
SAFETY_DAYS_DEFAULT = 3 # 결품 회피 강화(기존 2 → 3)

# 단가 기본표
BASE_UNIT_PRICE_BY_CATEGORY = {
    'Resistor': 10.0,'Capacitor': 12.0,'Inductor': 50.0,'Diode': 20.0,'Ferrite Bead': 15.0,
    'Misc IC / Unknown': 200.0,'PMIC / Power IC': 500.0,'RF Filter / Duplexer': 300.0,
    'RF Filter / Module': 800.0,'RF Front-End / PA': 1000.0,'Unknown': 100.0,
}
SIZE_PRICE_FACTOR = {'0402':1.0,'0604':1.2,'2015':5.0,'2520':6.0,'1008':1.4}

# SMT 사용 비중(카테고리×사이즈): 합=대략 1.0
CATEGORY_SHARE = {
    'Resistor':0.35,'Capacitor':0.30,'Inductor':0.05,'Diode':0.05,'Ferrite Bead':0.05,
    'Misc IC / Unknown':0.04,'PMIC / Power IC':0.04,'RF Filter / Duplexer':0.04,
    'RF Filter / Module':0.035,'RF Front-End / PA':0.025,'Unknown':0.035
}
SIZE_SHARE = {'0402':0.50,'0604':0.30,'1008':0.10,'2015':0.05,'2520':0.05}

# 지역/운송/월별 베이스 할인
MANUFACTURER_REGION = {'samsung':'KR','murata':'KR'}
REGION_FEE_RATE = {'KR':0.02}
SHIPPING_RATE = 0.05
BASE_MAX_DISCOUNT = 0.20  # 월별 베이스 할인 최대치

# 월별 제조사 대량발주 추가 할인
BULK_DISCOUNT_RANGE = (0.03, 0.05)      # -3% ~ -5%
BULK_THRESHOLD_K = 50                    # 해당 월 제조사에 50k 이상 주문 시 적용

# 주문 수량 불일치 이벤트
SPECIAL_EVENTS = {
    "order_mismatch_prob": 0.08,
    "order_mismatch_min_factor": 0.5,
    "order_mismatch_max_factor": 1.5,
}

# ------------------------- 유틸 함수 -------------------------
# 카테고리/사이즈 정규화
_KOR2ENG_CATEGORY = {
    "저항": "Resistor",
    "커패시터": "Capacitor",
    "인덕터": "Inductor",
    "다이오드": "Diode",
    "페라이트 비드": "Ferrite Bead",
    "전원 IC": "PMIC / Power IC",
    "파워 IC": "PMIC / Power IC",
    "RF 필터/듀플렉서": "RF Filter / Duplexer",
    "RF 모듈": "RF Filter / Module",
    "RF 프론트엔드/PA": "RF Front-End / PA",
}

def _norm_category(c: str) -> str:
    c = str(c).strip()
    return _KOR2ENG_CATEGORY.get(c, c)

def _norm_size(s: str) -> str:
    s = str(s).strip()
    if len(s) == 3 and s in {"402", "604"}:
        return "0" + s   # 402 → 0402, 604 → 0604
    return s

def _unit_price(cat: str, size: str) -> float:
    base = BASE_UNIT_PRICE_BY_CATEGORY.get(cat, 100.0)
    fac  = SIZE_PRICE_FACTOR.get(str(size), 1.0)
    return float(base*fac)

def _region_rate(manu: str) -> float:
    return REGION_FEE_RATE.get(MANUFACTURER_REGION.get(str(manu).lower(),'KR'), 0.02)

def _round_pack(q, pack=PACK_SIZE):
    if q <= 0: return 0
    return int(np.ceil(q/pack)*pack)

def _safe_int(x, default=0):
    try: return int(x)
    except Exception: return default

def _fetch_parts_meta() -> Dict[int, dict]:
    rows = query_db("SELECT part_id, category, size, manufacturer FROM pcb_parts ORDER BY part_id")
    if not rows:
        raise RuntimeError("DB에서 부품 메타를 읽지 못했습니다.")
    out = {}
    for r in rows:
        pid = int(r["part_id"])
        # ★ 정규화 추가
        cat  = _norm_category(r.get("category", "Unknown"))
        size = _norm_size(r.get("size", "Unknown"))
        manu = str(r.get("manufacturer", "unknown")).lower().strip() or "unknown"
        out[pid] = {"category": cat, "size": size, "manufacturer": manu}
    print(f"[DB] parts meta 로드: {len(out)}개")
    return out


def _build_part_weights(parts_meta: Dict[int,dict]) -> Dict[int, float]:
    # 카테고리×사이즈 share를 곱하여 파트별 weight 산출 → 정규화
    raw = {}
    for pid, m in parts_meta.items():
        w = CATEGORY_SHARE.get(m["category"], 0.01) * SIZE_SHARE.get(str(m["size"]), 0.05)
        raw[pid] = w
    s = sum(raw.values()) or 1.0
    return {pid: (w/s) for pid, w in raw.items()}

# ------------------------- 메인 생성 로직 -------------------------
def generate_year_data(year: int, data_root: str, smt_mode: str,
                       init_k_min: int, init_k_max: int,
                       daily_k_min: int, daily_k_max: int,
                       safety_days: int, seed: int):
    rng = np.random.default_rng(seed + (year-2000))
    dates = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")

    parts_meta = _fetch_parts_meta()
    part_weights = _build_part_weights(parts_meta)

    # 월별 베이스 할인(제조사 무관) + 월별 "프로모션 제조사" 선택
    monthly_base_discount = {m: float(rng.uniform(0.0, BASE_MAX_DISCOUNT)) for m in range(1,13)}
    monthly_promo_manufacturer = {m: rng.choice(["samsung","murata"]) for m in range(1,13)}
    monthly_promo_extra = {m: float(rng.uniform(*BULK_DISCOUNT_RANGE)) for m in range(1,13)}

    # 초기 재고(k단위 가중 랜덤)
    init_stock = {}
    for pid, w in part_weights.items():
        base_k = init_k_min + w*(init_k_max - init_k_min)
        base_k = int(max(init_k_min, round(base_k + rng.normal(0, 2))))
        init_stock[pid] = max(0, base_k) * 1000  # k → ea

    # 리드타임 큐(1일), 사용 히스토리
    inbound_q = {pid: deque([0]*LEAD_TIME_DAYS, maxlen=LEAD_TIME_DAYS) for pid in parts_meta}
    usage_hist = {pid: [] for pid in parts_meta}
    stock_prev = init_stock.copy()

    unit_price_map = {pid: _unit_price(parts_meta[pid]["category"], parts_meta[pid]["size"]) for pid in parts_meta}
    region_rate_map= {pid: _region_rate(parts_meta[pid]["manufacturer"]) for pid in parts_meta}

    recs_by_pid: Dict[int, list] = defaultdict(list)

    # 월별 누적 발주량(제조사별, 대량발주 할인 판정용)
    monthly_order_by_manu = defaultdict(int)

    for d in dates:
        m = d.month
        base_disc = monthly_base_discount[m]
        promo_manu = monthly_promo_manufacturer[m]
        promo_extra = monthly_promo_extra[m]

        # 일일 총 SMT 사용량(k단위)을 계절성+잡음으로 생성 → ea
        total_k = rng.integers(daily_k_min, daily_k_max+1)
        # 약간의 월주기(±15%) 추가
        total_k = max(daily_k_min, int(total_k*(1.0 + 0.15*np.sin(2*np.pi*(d.timetuple().tm_yday/30)))))
        total_usage_ea = int(total_k * 1000)

        # 파트별 계획 사용량 = 총량 × weight (반올림)
        planned_usage = {}
        for pid, w in part_weights.items():
            planned_usage[pid] = int(round(total_usage_ea * w))

        # 월이 바뀌면 제조사별 누적 발주량 초기화
        if d.day == 1:
            monthly_order_by_manu.clear()

        for pid in parts_meta:
            manu = parts_meta[pid]["manufacturer"]
            up   = unit_price_map[pid]

            op = stock_prev[pid] + (inbound_q[pid].popleft() if LEAD_TIME_DAYS>0 else 0)
            plan = planned_usage.get(pid, 0)
            used = min(plan, op)
            unmet= max(0, plan - used)
            close= op - used

            # 최근7일 평균 사용량 기반 ROP
            usage_hist[pid].append(used)
            ma7 = float(np.mean(usage_hist[pid][-7:])) if usage_hist[pid] else float(plan)
            rop = int(ma7 * (LEAD_TIME_DAYS + safety_days))

            pending = sum(inbound_q[pid]) if LEAD_TIME_DAYS>0 else 0
            order_req = 0
            if (close + pending) <= rop:
                target = max(rop + int(ma7 * safety_days), rop*2)  # 충분 버퍼
                base_need = max(0, target - (close + pending))
                order_req = _round_pack(max(MOQ, base_need), PACK_SIZE)

            # 이벤트: 발주 수량 불일치
            order_eff = order_req
            if order_req>0 and rng.random() < SPECIAL_EVENTS["order_mismatch_prob"]:
                f = float(rng.uniform(SPECIAL_EVENTS["order_mismatch_min_factor"], SPECIAL_EVENTS["order_mismatch_max_factor"]))
                order_eff = int(max(0, round(order_req * f)))

            # 대량발주 추가 할인 판정(해당 월 제조사 + 임계 이상 누적)
            eff_discount = base_disc
            if order_eff > 0 and manu == promo_manu:
                monthly_order_by_manu[manu] += order_eff
                if monthly_order_by_manu[manu] >= BULK_THRESHOLD_K*1000:
                    eff_discount = min(0.9, base_disc + promo_extra)  # 누적이 크면 더 큰 할인 유지

            goods_cost  = up * (1 - eff_discount) * order_eff
            shipping_fee= goods_cost * SHIPPING_RATE
            region_fee  = goods_cost * region_rate_map[pid]
            total_cost  = goods_cost + shipping_fee + region_fee

            if LEAD_TIME_DAYS>0:
                inbound_q[pid].append(order_eff)

            recs_by_pid[pid].append({
                "date": d.strftime("%Y-%m-%d"),
                "part_id": pid,
                "category": parts_meta[pid]["category"],
                "size": parts_meta[pid]["size"],
                "manufacturer": manu,
                "opening_stock": op,
                "arrival_today": inbound_q[pid][0] if LEAD_TIME_DAYS>0 else 0, # 내일 도착예정
                "planned_usage": plan,
                "used_actual": used,
                "unmet_usage": unmet,
                "closing_stock": close,
                "pending_inbound_before_order": pending,
                "order_qty_requested": order_req,
                "order_qty_effective": order_eff,
                "lead_time_days": LEAD_TIME_DAYS,
                "unit_price": round(up,2),
                "monthly_discount": round(eff_discount,4),
                "shipping_fee": round(shipping_fee,2),
                "region_fee": round(region_fee,2),
                "total_cost": round(total_cost,2),
            })
            stock_prev[pid] = close

    # 저장
    year_dir = os.path.join(data_root, str(year))
    os.makedirs(year_dir, exist_ok=True)
    for pid, rows in recs_by_pid.items():
        dfp = pd.DataFrame(rows).sort_values("date")
        calc_close = dfp["opening_stock"] - dfp["used_actual"]
        assert calc_close.equals(dfp["closing_stock"]), f"재고 등식 불일치: pid={pid}"
        out = os.path.join(year_dir, f"Part_{pid}.csv")
        dfp.to_csv(out, index=False)
    print(f"[{year}] 저장 완료: {year_dir} ({len(recs_by_pid)} parts)")

def _reset_outputs(root: str, years: List[int]):
    # data/*/*.csv 전체 리셋
    for y in years:
        yd = os.path.join(root, str(y))
        if os.path.isdir(yd): shutil.rmtree(yd)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", type=str, default="2022,2023,2024")
    ap.add_argument("--smt_mode", choices=["weight","bom"], default="weight", help="weight: 비중 기반(권장), bom: 기존 BOM 경로")
    ap.add_argument("--init-k-min", type=int, default=5)
    ap.add_argument("--init-k-max", type=int, default=50)
    ap.add_argument("--daily-k-min", type=int, default=10)
    ap.add_argument("--daily-k-max", type=int, default=40)
    ap.add_argument("--safety-days", type=int, default=SAFETY_DAYS_DEFAULT)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--no-reset", action="store_true")
    ap.add_argument("--pcb-csv", type=str, default="PCB_SMT.csv", help="smt_mode=bom 일 때 사용")
    args = ap.parse_args()

    years = [int(x.strip()) for x in args.years.split(",") if x.strip()]
    data_root = "data"
    os.makedirs(data_root, exist_ok=True)
    if not args.no_reset:
        _reset_outputs(data_root, years)

    if args.smt_mode == "bom":
        # (옵션) 기존 BOM 모드 유지가 필요할 때 → 기존 로직으로 대체 가능
        raise NotImplementedError("현재 버전은 weight 모드를 권장합니다. 필요 시 bom 모드 코드를 추가하세요.")
    else:
        for y in years:
            generate_year_data(
                year=y, data_root=data_root, smt_mode="weight",
                init_k_min=args.init_k_min, init_k_max=args.init_k_max,
                daily_k_min=args.daily_k_min, daily_k_max=args.daily_k_max,
                safety_days=args.safety_days, seed=args.seed
            )
    print("모든 연도 데이터 생성 완료.")

if __name__ == "__main__":
    main()
