# config/settings.py - 애플리케이션 설정

# AI 모델 설정
AI_MODEL_CONFIG = {
    "rf_reg": 200,
    "rf_days": 200, 
    "rf_cls": 200,
    "max_depth": None,
    "horizon": 30,
    "service_days": 14,
    "pack_size": 100,
    "moq": 0,
    "holding_rate_per_day": 0.0005,
    "penalty_multiplier": 5.0,
    "event_prob": 0.08,
    "event_range": (0.03, 0.08)
}

# 데이터 처리 설정
DATA_CONFIG = {
    "train_years": [2023, 2024],
    "eval_split": 0.2,
    "sample_rate": 1.0
}

# API 설정
API_CONFIG = {
    "default_limit": 100,
    "max_limit": 1000,
    "timeout": 180
}

# 로깅 설정
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "logs/app.log"
}
