FROM python:3.11-slim

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc g++ curl \
    # PyTorch 의존성
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 요구사항 설치
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 폴더 생성
RUN mkdir -p /app/CNN_model /app/LLM_model /app/excel_data \
    /app/data/2022 /app/data/2023 /app/data/2024 \
    /app/model_all /app/services

# 소스 코드 복사
COPY . /app/

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py

# 포트 노출
EXPOSE 5000 5100

# 실행 명령
CMD ["gunicorn", "-w", "2", "-k", "gthread", "--threads", "4", \
     "--timeout", "180", "-b", "0.0.0.0:5100", "app:app"]