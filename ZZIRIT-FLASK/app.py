from flask import Flask, jsonify
from flask_cors import CORS
import os
from datetime import datetime
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# Blueprint imports
from api.chat_1 import chat1_bp
from api.chat_4 import chat4_bp
from api.ai.cnn import pcbai_bp
from api.utils.email import email_bp
from api.ai.prediction import ai_bp

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
app.register_blueprint(chat1_bp, url_prefix="/api")
app.register_blueprint(chat4_bp, url_prefix="/api")
app.register_blueprint(email_bp, url_prefix="/api")
app.register_blueprint(pcbai_bp, url_prefix="/api")
app.register_blueprint(ai_bp)  # url_prefix는 ai_bp에서 정의됨

@app.route("/")
def index():
    return jsonify({
        "status": "✅ ZZIRIT-FLASK 서버 실행 중",
        "version": "1.0.0",
        "endpoints": {
            "main_chat": "/api/chat",           # chat1 (메인 완성)
            "ai_prediction": "/api/predict",    # api_server (완성)
            "inventory": "/api/inventory-chat", # chat4 (개발중)
            "pcb_defect": "/api/pcb",          # cnn (개발중)
            "email": "/api/send-email",        # send_email (개발중)
            "health": "/api/health"
        },
        "services": {
            "완성": ["main_chat", "ai_prediction"],
            "개발중": ["inventory", "pcb_defect", "email", "advanced_chat"]
        }
    })

@app.route("/health")
def health():
    try:
        # 기본 서비스 체크
        services = {
            "app": "running",
            "main_chat": "available",
            "ai_prediction": "available"
        }
        
        # DB 연결 체크
        try:
            from services.database.models import get_db_connection
            conn = get_db_connection()
            conn.close()
            services["database"] = "connected"
        except:
            services["database"] = "disconnected"
        
        # Gemini API 체크
        try:
            from services.external.gemini import get_api_status
            gemini_status = get_api_status()
            services["gemini_api"] = "ready" if gemini_status.get('ready') else "not_ready"
        except:
            services["gemini_api"] = "not_configured"
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": services
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5100))
    debug_mode = os.getenv("FLASK_ENV") == "development"
    
    print("=" * 60)
    print(f"✅ ZZIRIT-FLASK 서버 시작: http://localhost:{port}")
    print("📋 사용 가능한 서비스:")
    print("  ✅ 메인 채팅 (chat1) - 완성")
    print("  ✅ AI 예측 (api_server) - 완성")
    print("  🚧 재고 관리 (chat4) - 개발중")
    print("  🚧 PCB 불량 검사 (cnn) - 개발중")
    print("  🚧 이메일 발송 (send_email) - 개발중")
    print("  🚧 고급 채팅 (chat2-3) - 개발중")
    print("=" * 60)
    
    app.run(host="0.0.0.0", port=port, debug=debug_mode)