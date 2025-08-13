# services/ai/predictor.py - AI 예측 서비스

import os, time
from typing import Any, Dict, List
import joblib
import numpy as np
import pandas as pd
from flask import jsonify

from .model_trainer import _norm_category, _norm_size, _norm_manufacturer
from dataclasses import dataclass

MODEL_DIR = os.environ.get("MODEL_DIR", "model_all")
BUNDLE_PATH = os.path.join(MODEL_DIR, "model_bundle.pkl")

@dataclass
class PartState:
    part_id: int
    opening_stock: float
    lead_time_days: int = 1
    pack_size: int = 100
    moq: int = 0

class AIPredictor:
    """AI 예측 서비스 클래스"""
    
    def __init__(self):
        self._bundle = None
        self._meta = None
        self._last_meta_ts = 0.0
    
    def _load_bundle(self):
        """모델 번들 로드 (싱글톤 패턴)"""
        if self._bundle is None:
            t0 = time.time()
            self._bundle = joblib.load(BUNDLE_PATH, mmap_mode="r")
            self._meta = self._bundle.get("meta", {})
            self._last_meta_ts = time.time()
            print(f"[model] loaded in {time.time()-t0:.2f}s, features={len(self._bundle.get('feature_columns', []))}")
        return self._bundle
    
    def _build_X_predict(self, rows: pd.DataFrame, feat_cols: List[str]) -> pd.DataFrame:
        """예측용 피처 행렬 구성"""
        base = [
            "opening_stock", "planned_usage", "used_actual", "pending_inbound_before_order",
            "lead_time_days", "dow", "month", "rolling7_used", "rolling30_used",
            "lag1_used", "lag7_used", "lag30_used", "roll7_std_used", "roll30_std_used",
            "unit_price", "monthly_discount", "shipping_fee", "region_fee"
        ]
        for c in base:
            if c not in rows.columns: 
                rows[c] = 0.0
        
        rows2 = rows[base + ["category", "size", "manufacturer"]].copy()
        X = pd.get_dummies(rows2, columns=["category", "size", "manufacturer"], drop_first=True)
        
        for col in feat_cols:
            if col not in X.columns: 
                X[col] = 0
        
        X = X[feat_cols]
        return X
    
    def _pick_model(self, models_by_group: dict, cat: str, size: str, man: str):
        """그룹별 모델 선택"""
        key = (cat, size, man)
        if key in models_by_group: 
            return models_by_group[key]
        
        for (c, s, m), mdl in models_by_group.items():
            if c == cat and s == size: 
                return mdl
        
        return next(iter(models_by_group.values()))
    
    def _price_forecast_simple(self, unit_price: float, horizon: int) -> np.ndarray:
        """간단한 가격 예측"""
        base = float(unit_price) if unit_price > 0 else 100.0
        rng = np.random.default_rng(123)
        return base * (1.0 + rng.normal(0, 0.002, size=horizon))
    
    def _demand_forecast_from_pred(self, mu: float, horizon: int) -> np.ndarray:
        """수요 예측"""
        return np.full(horizon, float(max(mu, 0.0)), dtype=float)
    
    def optimize_order_day_quantity(self, state: PartState, demand: np.ndarray, price: np.ndarray,
                                    horizon=30, service_days=14, holding_rate_per_day=0.0005,
                                    penalty_mult=5.0):
        """최적 발주 일정 및 수량 계산"""
        H = min(horizon, len(demand), len(price))
        if H <= 0: 
            return []
        
        out = []
        for d in range(H):
            arr = d + state.lead_time_days
            pre = demand[:min(arr, H)].sum()
            stock_at_arr = state.opening_stock - pre
            unit = float(price[d])
            penalty = max(0.0, -stock_at_arr) * unit * penalty_mult

            need = demand[arr:min(arr+service_days, H)].sum()
            base_q = max(0.0, need - max(0.0, stock_at_arr))
            q = int(max(base_q, state.moq))
            if state.pack_size > 0:
                q = int(np.ceil(q/state.pack_size)*state.pack_size)

            purchase = unit * q
            window = demand[arr:min(arr+service_days, H)]
            avg_consumed = window.mean() * len(window) if len(window) else 0.0
            avg_carry = max(0.0, q - avg_consumed)
            holding = holding_rate_per_day * unit * avg_carry * max(1, len(window))
            total = purchase + holding + penalty
            out.append((total, d, q, unit, penalty, holding))
        
        out.sort(key=lambda x: x[0])
        return [{"day_offset": int(d), "quantity": int(q), "expected_unit_price": round(p, 4),
                 "expected_total_cost": round(t, 2), "stockout_penalty": round(pen, 2),
                 "holding_cost": round(h, 2)} for (t, d, q, p, pen, h) in out[:3]]
    
    def predict(self, request_data):
        """AI 예측 실행"""
        try:
            args = request_data or {}
            
            # 모델 로드
            b = self._load_bundle()
            models = b["models"]
            feats = b["feature_columns"]
            
            # 예시 데이터 (실제로는 DB에서 가져와야 함)
            # TODO: DB 연결하여 실제 데이터 로드
            limit = int(args.get("limit", 100))
            rows = pd.DataFrame([{
                "part_id": i+1, 
                "category": "Capacitor" if i%2==0 else "Resistor",
                "size": "0402", 
                "manufacturer": "samsung" if i%3==0 else "murata",
                "quantity": (i%30)*100 + 2000, 
                "used_actual": (i%7)*5
            } for i in range(limit)])
            
            # 입력 정규화
            for c in ["part_id", "category", "size", "manufacturer", "quantity"]:
                if c not in rows.columns: 
                    rows[c] = None
            
            now = pd.Timestamp("today")
            rows["dow"] = now.dayofweek
            rows["month"] = now.month
            rows = rows.rename(columns={"quantity": "opening_stock"})
            rows["opening_stock"] = rows["opening_stock"].clip(lower=0)
            
            # 정규화
            if "category" in rows.columns:
                rows["category"] = rows["category"].map(_norm_category)
            if "size" in rows.columns:
                rows["size"] = rows["size"].map(_norm_size)
            if "manufacturer" in rows.columns:
                rows["manufacturer"] = rows["manufacturer"].map(_norm_manufacturer)
            
            X = self._build_X_predict(rows, feats)
            
            horizon = int(args.get("horizon", 30))
            svc = int(args.get("service_days", 14))
            hold = float(args.get("holding_rate_per_day", 0.0005))
            pen_mult = float(args.get("penalty_multiplier", 5.0))
            pack = int(args.get("pack_size", 100))
            moq = int(args.get("moq", 0))
            
            items = []
            for i, r in rows.iterrows():
                cat, size, man = r["category"], str(r["size"]), str(r["manufacturer"])
                mdl = self._pick_model(models, cat, size, man)
                Xi = X.iloc[[i]]
                
                # 30일 사용량 / 소진일
                usage30 = float(mdl["reg_usage"].predict(Xi)[0])
                days = float(mdl["reg_days"].predict(Xi)[0])
                
                # 단가(없으면 100)
                unit_price = float(r.get("unit_price", 0.0) or 100.0)
                demand_vec = self._demand_forecast_from_pred(max(usage30/horizon, 0.0), horizon)
                price_vec = self._price_forecast_simple(unit_price, horizon)
                
                state = PartState(int(r["part_id"]), float(r["opening_stock"]), 
                                  int(r.get("lead_time_days", 1)), pack, moq)
                recos = self.optimize_order_day_quantity(state, demand_vec, price_vec, 
                                                        horizon=horizon, service_days=svc, 
                                                        holding_rate_per_day=hold, penalty_mult=pen_mult)
                
                # 프론트 호환 필드
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
                    "best_day_top3": [{"day_offset": (best or {"day_offset": 0})["day_offset"], "prob": 0.65}] if best else []
                })
            
            # 카테고리별 커버 일수 요약
            df = pd.DataFrame(items)
            cats = []
            if not df.empty:
                for c, g in df.groupby("category"):
                    d = float(np.nanmean(g["predicted_days_to_depletion"])) if len(g) else None
                    cats.append({"category": c, "days_possible": None if d is None else round(d, 1)})
            
            result = {
                "generated_at": pd.Timestamp.utcnow().isoformat(),
                "n_parts": len(items),
                "items": items,
                "summary": {"categories": cats}
            }
            
            return jsonify(result), 200
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    def get_model_meta(self):
        """모델 메타데이터 조회"""
        try:
            self._load_bundle()
            # 3초 캐시
            if time.time() - self._last_meta_ts > 3:
                self._last_meta_ts = time.time()
            return jsonify({
                "available": True, 
                "meta": self._meta, 
                "updated_at": self._meta.get("created_at")
            })
        except Exception as e:
            return jsonify({"available": False, "error": str(e)}), 500
