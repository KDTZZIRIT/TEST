# CNN 모델 관리

이 폴더는 PCB 불량 검사를 위한 CNN 모델들을 관리합니다.

## 폴더 구조

```
models/cnn/
├── weights/           # 학습된 모델 가중치 (.pt, .pth 파일)
├── configs/           # 모델 설정 파일
├── checkpoints/       # 체크포인트 파일들
└── README.md         # 이 파일
```

## 모델 파일 배치

CNN 모델 파일을 받으신 후 다음과 같이 배치하세요:

1. **모델 가중치 파일**: `weights/` 폴더에 배치
   - 예: `best_model_by_confidence.pt`
   
2. **설정 파일**: `configs/` 폴더에 배치
   - 모델 아키텍처 설정 파일

3. **체크포인트**: `checkpoints/` 폴더에 배치
   - 학습 중간 저장 파일들

## API에서 사용되는 경로

현재 API 코드에서는 다음 경로를 참조하고 있습니다:
- `CNN_model/best_model_by_confidence.pt`

모델 파일을 배치한 후 API 코드의 경로를 업데이트하거나, 
심볼릭 링크를 생성하여 연결할 수 있습니다.
