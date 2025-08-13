#!/bin/bash

echo "🚀 ZZIRIT-FLASK 초기 설정 시작..."

# 1. 필요한 폴더 생성
echo "📁 폴더 생성 중..."
mkdir -p CNN_model LLM_model excel_data
mkdir -p data/{2022,2023,2024}
mkdir -p model_all

# 2. Python 가상환경 생성
echo "🐍 Python 가상환경 생성..."
python3 -m venv .venv
source .venv/bin/activate

# 3. 패키지 설치
echo "📦 패키지 설치 중..."
pip install --upgrade pip
pip install -r requirements.txt

# 4. 환경 변수 파일 생성
if [ ! -f .env ]; then
    echo "📝 .env 파일 생성..."
    cp .env.example .env
    echo "⚠️  .env 파일을 열어 API 키를 설정해주세요!"
fi

# 5. DB 테이블 확인
echo "🗄️ DB 연결 테스트..."
python -c "from db_handler import get_db_connection; conn = get_db_connection(); print('✅ DB 연결 성공'); conn.close()"

# 6. 초기 데이터 생성
echo "📊 초기 데이터 생성..."
python data3.py --years 2022,2023,2024

# 7. 모델 학습
echo "🤖 AI 모델 학습..."
python ai-5-4.py --retrain --years 2023,2024

echo "✅ 설정 완료! 다음 명령으로 서버를 시작하세요:"
echo "python app.py"