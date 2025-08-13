from flask import Flask, jsonify
from flask_cors import CORS
from api.chat_2 import chat_bp
from api.chat_1 import chat1_bp
from api.chat_4 import chat4_bp
from api.cnn import pcbai_bp
from api.send_email import email_bp
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# CORS 설정
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "http://127.0.0.1:3000", "*"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Blueprint 등록
app.register_blueprint(chat_bp, url_prefix="/api")
app.register_blueprint(chat1_bp, url_prefix="/api")
app.register_blueprint(chat4_bp, url_prefix="/api")
app.register_blueprint(email_bp, url_prefix="/api")
app.register_blueprint(pcbai_bp, url_prefix="/api")

@app.route("/")
def index():
    return jsonify({
        "status": "✅ Flask 서버 실행 중입니다.",
        "endpoints": {
            "chat": "/api/llm",
            "health": "/api/health"
        }
    })

@app.route("/api/hello")
def hello():
    return jsonify({"message": "Hello from Flask!"})

# 디버깅을 위한 등록된 라우트 확인
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

# 전역 오류 처리
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5100))
    
    print("=" * 60)
    print(f"✅ Flask 서버가 http://localhost:{port} 에서 실행 중입니다.")
    print(f"✅ HTTP API: http://localhost:{port}/api/llm")
    print(f"✅ 헬스체크: http://localhost:{port}/api/health")
    print(f"✅ Gemini AI 챗봇이 준비되었습니다.")
    print("=" * 60)
    
    # 개발 모드에서는 debug=True, 프로덕션에서는 debug=False
    debug_mode = os.environ.get("FLASK_ENV") == "development"
    
    app.run(
        host="0.0.0.0", 
        port=port, 
        debug=debug_mode
    )
