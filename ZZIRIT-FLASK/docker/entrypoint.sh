#!/bin/bash

echo "🚀 ZZIRIT-FLASK Docker 컨테이너 시작..."

# 환경 변수 확인
check_env_var() {
    if [ -z "${!1}" ]; then
        echo "❌ 환경 변수 $1이 설정되지 않았습니다."
        return 1
    else
        echo "✅ $1: 설정됨"
        return 0
    fi
}

echo "📋 환경 변수 확인 중..."
ENV_CHECK=0

# 필수 환경 변수 확인
if ! check_env_var "GEMINI_API_KEY"; then ENV_CHECK=1; fi

if [ $ENV_CHECK -eq 1 ]; then
    echo "⚠️ 일부 환경 변수가 설정되지 않았지만 계속 진행합니다."
    echo "📝 .env 파일을 확인해주세요."
fi

# 필요한 폴더 확인/생성
echo "📁 폴더 구조 확인 중..."
mkdir -p CNN_model LLM_model model_all logs
mkdir -p data/2022 data/2023 data/2024

# DB 연결 테스트 (선택적)
echo "🗄️ 데이터베이스 연결 테스트..."
python -c "
import sys
try:
    from services.database.models import get_db_connection
    conn = get_db_connection()
    conn.close()
    print('✅ DB 연결 성공')
except Exception as e:
    print(f'⚠️ DB 연결 실패: {e}')
    print('계속 진행하지만 DB 기능은 제한될 수 있습니다.')
" || echo "⚠️ DB 연결 테스트를 건너뜁니다."

# Gemini API 테스트 (선택적)
echo "🤖 Gemini API 연결 테스트..."
python -c "
import sys
try:
    from services.external.gemini import get_api_status
    status = get_api_status()
    if status.get('ready'):
        print('✅ Gemini API 준비됨')
    else:
        print('⚠️ Gemini API 설정 확인 필요')
except Exception as e:
    print(f'⚠️ Gemini API 테스트 실패: {e}')
" || echo "⚠️ Gemini API 테스트를 건너뜁니다."

echo "🎯 ZZIRIT-FLASK 서버 시작 준비 완료"
echo "================================================================="

# 인자가 없으면 기본 gunicorn 실행
if [ $# -eq 0 ]; then
    echo "🚀 Gunicorn으로 서버 시작..."
    exec gunicorn -w 2 -k gthread --threads 4 --timeout 180 --bind 0.0.0.0:5100 app:app
else
    echo "🚀 커스텀 명령 실행: $@"
    exec "$@"
fi
