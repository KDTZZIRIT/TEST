FROM python:3.11-slim

# 시스템 의존성
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc g++ curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 소스
COPY ai-5-4.py api_server.py data3.py db_handler.py db_config.py /app/
RUN mkdir -p /app/model_all

# gunicorn으로 Flask 서빙
EXPOSE 5000
CMD ["gunicorn", "-w", "1", "-k", "gthread", "--threads", "4", "--timeout", "180", "-b", "0.0.0.0:5000", "api_server:app"]
