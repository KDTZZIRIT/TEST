# scripts/train_model.py - AI 모델 학습 스크립트

import argparse
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.ai.model_trainer import ModelTrainer, load_annual_category_data

def main():
    parser = argparse.ArgumentParser(description="AI 모델 학습")
    
    # 기본 옵션
    parser.add_argument("--years", type=str, default="2023,2024", help="학습에 사용할 연도 (쉼표로 구분)")
    parser.add_argument("--data-root", type=str, default="data", help="데이터 루트 디렉토리")
    parser.add_argument("--model-dir", type=str, default="model_all", help="모델 저장 디렉토리")
    
    # 모델 설정
    parser.add_argument("--rf-reg", type=int, default=200, help="회귀 모델 트리 수")
    parser.add_argument("--rf-days", type=int, default=200, help="소진일 모델 트리 수")
    parser.add_argument("--rf-cls", type=int, default=200, help="분류 모델 트리 수")
    parser.add_argument("--max-depth", type=int, default=None, help="트리 최대 깊이")
    
    # 평가 옵션
    parser.add_argument("--eval-mae", action="store_true", help="훈련 중 홀드아웃으로 예측/발주 MAE 출력")
    parser.add_argument("--eval-split", type=float, default=0.2, help="홀드아웃 비율")
    
    # 확률 이벤트
    parser.add_argument("--event-prob", type=float, default=0.08, help="확률 이벤트 발생 확률")
    parser.add_argument("--event-range", nargs=2, type=float, default=None, metavar=("LOW", "HIGH"), help="이벤트 범위")
    
    # 기타
    parser.add_argument("--save-meta", action="store_true", help="모델 메타데이터 저장")
    parser.add_argument("--compress", type=int, default=3, help="모델 압축 레벨")
    parser.add_argument("--sample-rate", type=float, default=1.0, help="데이터 샘플링 비율")
    
    args = parser.parse_args()
    
    # 연도 파싱
    years = [int(x.strip()) for x in args.years.split(",") if x.strip()]
    print(f"학습 대상 연도: {years}")
    
    try:
        # 데이터 로드
        print("데이터 로드 중...")
        df_all = load_annual_category_data(args.data_root, years=years)
        
        # 샘플링 (필요시)
        if 0.0 < args.sample_rate < 1.0:
            frac = max(0.0, min(1.0, args.sample_rate))
            df_all = df_all.sample(frac=frac, random_state=42).reset_index(drop=True)
            print(f"데이터 샘플링: {len(df_all)}행")
        
        print(f"총 데이터: {len(df_all)}행, {df_all['part_id'].nunique()}개 부품")
        
        # 모델 학습
        print("모델 학습 시작...")
        trainer = ModelTrainer(args.model_dir)
        model_path = trainer.train_and_save_models(df_all, args)
        
        print(f"✅ 학습 완료! 모델 저장: {model_path}")
        
    except Exception as e:
        print(f"❌ 학습 실패: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()