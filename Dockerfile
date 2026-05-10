FROM python:3.11-slim

WORKDIR /app

# Pillow 사용을 고려해 최소한의 이미지 처리 라이브러리 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "app.main"]
