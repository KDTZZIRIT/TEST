from flask import Flask, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# Blueprint imports
from api.chat_2 import chat_bp
from api.chat_1 import chat1_bp
from api.chat_4 import chat4_bp  # chat_3 대신 chat_4 사용
from api.cnn import pcbai_bp
from api.send_email import email_bp

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')

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
app.register_blueprint(chat4_bp, url_prefix="/api")  # 통합된 inventory chat
app.register_blueprint(email_bp, url_prefix="/api")
app.register_blueprint(pcbai_bp, url_prefix="/api")

# 추가: API 서버 Blueprint 등록 (필요시)
# from api_server import predict
# app.add_url_rule('/api/predict', 'predict', predict, methods=['POST'])

@app.route("/")
def index():
    return jsonify({
        "status": "✅ ZZIRIT-FLASK 서버 실행 중",
        "version": "1.0.0",
        "endpoints": {
            "chat": "/api/llm",
            "inventory": "/api/inventory-chat",
            "pcb_defect": "/api/pcb",
            "email": "/api/send-email",
            "health": "/api/health"
        }
    })

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5100))
    debug_mode = os.getenv("FLASK_ENV") == "development"
    
    print("=" * 60)
    print(f"✅ Flask 서버 시작: http://localhost:{port}")
    print("=" * 60)
    
    app.run(host="0.0.0.0", port=port, debug=debug_mode)