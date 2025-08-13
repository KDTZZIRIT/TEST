from flask import Blueprint, request, jsonify
import torch
import torchvision
from torchvision.models.detection import fasterrcnn_resnet50_fpn
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
import numpy as np
from PIL import Image
import os
import requests
from io import BytesIO

pcbai_bp = Blueprint('pcbai', __name__)

class_names = [
    "missing_hole", "mouse_bite", "open_circuit", "short", "spur", "spurious_copper"
]

model = None
device = None

def load_model():
    global model, device
    try:
        print("🔍 PyTorch Faster R-CNN 모델 로딩 시도 중...")
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"📱 사용 디바이스: {device}")
        model_path = "CNN_model/best_model_by_confidence.pt"
        num_classes = 6
        if not os.path.exists(model_path):
            print(f"❌ 모델 파일이 존재하지 않습니다: {model_path}")
            return None
        print(f"📁 모델 파일 발견: {model_path}")
        model = fasterrcnn_resnet50_fpn(weights="DEFAULT")
        in_features = model.roi_heads.box_predictor.cls_score.in_features
        model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)
        model.to(device)
        model.load_state_dict(torch.load(model_path, map_location=device))
        model.eval()
        print("✅ Faster R-CNN 모델 로딩 완료!")
        return model
    except Exception as e:
        print(f"❌ 모델 로딩 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return None

def download_image_from_url(image_url):
    """URL에서 이미지 다운로드"""
    try:
        print(f"📥 이미지 다운로드 중: {image_url}")
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content)).convert("RGB")
        print(f"✅ 이미지 다운로드 완료: {image.size}")
        return image
    except Exception as e:
        print(f"❌ 이미지 다운로드 실패: {e}")
        raise e

def preprocess_image_from_url(image_url):
    """URL에서 이미지 다운로드 후 전처리: RGB, 0~1 정규화, torch tensor 변환"""
    try:
        print(f"🖼️ 이미지 전처리 중: {image_url}")
        image = download_image_from_url(image_url)
        image_np = np.array(image).astype(np.float32) / 255.0
        image_tensor = torch.from_numpy(image_np).permute(2, 0, 1)
        print(f"✅ 이미지 전처리 완료: {image_tensor.shape}")
        return image_tensor
    except Exception as e:
        print(f"❌ 이미지 전처리 실패: {e}")
        raise e

def process_faster_rcnn_predictions(predictions, confidence_threshold=0.3):
    try:
        print(f"🔍 Faster R-CNN 예측 결과 처리 중...")
        results = []
        defect_count = 0
        max_confidence = 0.0
        boxes = predictions[0]['boxes'].cpu().numpy()
        scores = predictions[0]['scores'].cpu().numpy()
        labels = predictions[0]['labels'].cpu().numpy()
        for i, (box, score, label) in enumerate(zip(boxes, scores, labels)):
            if score > max_confidence:
                max_confidence = score
            if score >= confidence_threshold:
                defect_count += 1
                if 0 <= label < len(class_names):
                    class_name = class_names[label]
                else:
                    class_name = f"unknown_class_{label}"
                defect_info = {
                    'label': class_name,
                    'score': round(float(score), 4),
                    'class_index': int(label),
                    'bbox': {
                        'x1': float(box[0]),
                        'y1': float(box[1]),
                        'x2': float(box[2]),
                        'y2': float(box[3]),
                        'width': float(box[2] - box[0]),
                        'height': float(box[3] - box[1])
                    }
                }
                results.append(defect_info)
        summary = {
            'total_defects': defect_count,
            'max_confidence': round(float(max_confidence), 4),
            'is_defective': defect_count > 0,
            'defects': results
        }
        print(f"✅ 결함 검출 완료: {defect_count}개 결함 발견")
        return summary
    except Exception as e:
        print(f"❌ 예측 결과 처리 실패: {e}")
        raise e

@pcbai_bp.route('/pcb', methods=['POST'])
def detect_defect():
    global model, device
    
    # JSON 요청에서 imageUrl 받기
    try:
        data = request.get_json()
        if not data or 'imageUrl' not in data:
            return jsonify({'error': 'imageUrl이 제공되지 않았습니다.'}), 400
        image_url = data['imageUrl']
        pcb_id = data['pcb_id']
        print('이미지 URL 받음:', image_url)
        print('PCB ID 받음:', pcb_id)
    except Exception as e:
        return jsonify({'error': '잘못된 JSON 형식입니다.'}), 400
    
    # 모델 로드 확인
    if model is None:
        print("🔄 모델 로딩 중...")
        model = load_model()
    if model is None:
        return jsonify({'error': '모델을 로드할 수 없습니다.'}), 500
    print("✅ 모델 로드 확인됨")
    
    # 이미지 전처리
    try:
        image_tensor = preprocess_image_from_url(image_url)
    except Exception as e:
        return jsonify({'error': f'이미지 처리 실패: {str(e)}'}), 400
    
    # 모델 예측
    try:
        print("🤖 AI 예측 중...")
        with torch.no_grad():
            predictions = model([image_tensor.to(device)])
        print(f"✅ 예측 완료")
    except Exception as e:
        print(f"❌ 예측 실패: {e}")
        return jsonify({'error': f'AI 예측 실패: {str(e)}'}), 500
    
    # 결과 처리
    try:
        results = process_faster_rcnn_predictions(predictions)
    except Exception as e:
        print(f"❌ 결과 처리 실패: {e}")
        return jsonify({'error': f'결과 처리 실패: {str(e)}'}), 500
    
    # 응답 생성
    if results['is_defective']:
        response = {
            'pcb_id': pcb_id,
            'image_url': image_url,
            'status': '불합격',
            'message': f'{results["total_defects"]}개의 결함이 감지되었습니다.',
            'defect_count': results['total_defects'],
            'max_confidence': results['max_confidence'],
            'defects': results['defects']
        }
    else:
        response = {
            'pcb_id': pcb_id,
            'image_url': image_url,
            'status': '합격',
            'message': '결함이 감지되지 않았습니다.',
            'defect_count': 0,
            'max_confidence': results['max_confidence'],
            'defects': []
        }
    print(f"🎯 최종 결과: {response['status']}")
    return jsonify(response)

# 서버 시작 시 모델 로드
print("🚀 PCB AI 서비스 시작 (Faster R-CNN)...")
model = load_model()
if model:
    print("✅ 모델 로드 완료!")
else:
    print("⚠️ 모델 로드 실패 - 요청 시 재시도됨")