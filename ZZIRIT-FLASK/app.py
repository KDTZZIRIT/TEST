from flask import Flask, jsonify, request  # request 추가
from flask_cors import CORS
from api.chat_2 import chat_bp
from api.chat_1 import chat1_bp
from api.chat_4 import chat4_bp

from api.send_email import email_bp
from api.api_server import api_bp as api_server_bp
import os
from dotenv import load_dotenv
import logging

# .env 파일 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": r".*"}}, supports_credentials=True)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# CORS 

# Blueprint 등록
app.register_blueprint(chat_bp, url_prefix="/api")
app.register_blueprint(chat1_bp, url_prefix="/api")
app.register_blueprint(chat4_bp, url_prefix="/api")
app.register_blueprint(email_bp, url_prefix="/api")

app.register_blueprint(api_server_bp, url_prefix="/api")

@app.route("/")
def index():
    return jsonify({
        "status": "✅ Flask 서버 실행 중입니다.",
        "endpoints": {
            "chat": "/api/llm",
            "health": "/api/health",
            "predict": "/api/predict"
        }
    })

@app.route("/api/hello")
def hello():
    return jsonify({"message": "Hello from Flask!"})

@app.route("/api/routes")
def list_routes():
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            "endpoint": rule.endpoint,
            "methods": list(rule.methods),
            "url": str(rule)
        })
    return jsonify({"routes": routes})

# 요청 로깅
@app.before_request
def log_request_info():
    logger.info(f"Request: {request.method} {request.path}")
    if request.method == 'POST' and request.get_json(silent=True):
        logger.debug(f"Payload: {request.get_json(silent=True)}")

# 전역 오류 처리
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled exception: {e}", exc_info=True)
    return jsonify({
        "error": "Internal server error",
        "message": str(e) if app.debug else "An error occurred"
    }), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5200))
    
    print("=" * 60)
    print(f"✅ Flask 서버가 http://localhost:{port} 에서 실행 중입니다.")
    print(f"✅ 예측 API: http://localhost:{port}/api/predict")
    print(f"✅ 헬스체크: http://localhost:{port}/api/health")
    print(f"✅ AI 예측 시스템이 준비되었습니다.")
    print("=" * 60)
    
    debug_mode = os.environ.get("FLASK_ENV") == "development"
    
    app.run(
        host="0.0.0.0", 
        port=port, 
        debug=debug_mode
    )
    ALLOWED_ORIGINS = {
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://192.168.0.10:3000",   # 현재 사용 중인 프론트 주소
}

@app.after_request
def add_cors_headers(resp):
    try:
        origin = request.headers.get("Origin")
        # /api/* 인 경우에만 적용 (다른 라우트 영향 없음)
        if origin in ALLOWED_ORIGINS and request.path.startswith("/api/"):
            resp.headers["Access-Control-Allow-Origin"] = origin
            resp.headers["Vary"] = "Origin"
            resp.headers["Access-Control-Allow-Credentials"] = "true"
            resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            resp.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    except Exception:
        pass
    return resp