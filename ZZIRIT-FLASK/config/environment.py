# config/environment.py - 환경변수 관리

import os
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

class Config:
    """기본 설정"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    MODEL_DIR = os.getenv('MODEL_DIR', 'model_all')
    DATA_DIR = os.getenv('DATA_DIR', 'data')
    
    # API 설정
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    
    # Flask 설정
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    PORT = int(os.getenv('PORT', 5100))
    
    # CORS 설정
    CORS_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    @classmethod
    def is_production(cls):
        return cls.FLASK_ENV == 'production'
    
    @classmethod
    def is_development(cls):
        return cls.FLASK_ENV == 'development'

class DevelopmentConfig(Config):
    """개발환경 설정"""
    DEBUG = True
    
class ProductionConfig(Config):
    """운영환경 설정"""
    DEBUG = False

# 환경에 따른 설정 선택
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
