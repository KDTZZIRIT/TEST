FROM python:3.11-slim

# 메타데이터
LABEL maintainer="ZZIRIT Team"
LABEL description="ZZIRIT PCB Management Flask API Server"

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc g++ curl \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python 요구사항 먼저 설치 (Docker 캐시 최적화)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 필요한 폴더 생성
RUN mkdir -p CNN_model LLM_model excel_data \
    data/2022 data/2023 data/2024 \
    model_all services logs

# 소스 코드 복사
COPY . .

# 실행 권한 부여 (필요한 스크립트들)
RUN chmod +x setup.sh || true
RUN chmod +x entrypoint.sh || true

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py
ENV PYTHONPATH=/app

# 포트 노출
EXPOSE 5100

# ✅ 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:5100/health || exit 1

# 실행 명령
CMD ["gunicorn", "-w", "2", "-k", "gthread", "--threads", "4", \
     "--timeout", "180", "--bind", "0.0.0.0:5100", "app:app"]