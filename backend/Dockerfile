FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (for ffmpeg, tesseract)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ && \
    pip config set global.trusted-host mirrors.aliyun.com && \
    pip install --upgrade pip && \
    pip install setuptools wheel && \
    pip install torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install "bcrypt>=4.0.1" && \
    pip install --no-build-isolation openai-whisper==20231117 && \
    pip install -r requirements.txt

COPY . .

RUN mkdir -p uploads data

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
