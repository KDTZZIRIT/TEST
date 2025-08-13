from flask import Blueprint, request, jsonify
from services.ai.predictor import AIPredictor

ai_bp = Blueprint('ai', __name__, url_prefix='/api/ai')

@ai_bp.route('/predict', methods=['POST'])
def predict():
    """AI 예측 API 엔드포인트"""
    predictor = AIPredictor()
    return predictor.predict(request.get_json())

@ai_bp.route('/model/meta', methods=['GET'])
def model_meta():
    """모델 메타데이터 조회 API"""
    predictor = AIPredictor()
    return predictor.get_model_meta()

@ai_bp.route('/health', methods=['GET'])
def health():
    """AI 서비스 헬스체크"""
    import os
    bundle_path = os.path.join(os.environ.get("MODEL_DIR", "model_all"), "model_bundle.pkl")
    ok = os.path.exists(bundle_path)
    return jsonify({"ok": ok, "model_available": ok})
