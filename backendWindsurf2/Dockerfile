# ExamAI Backend Dockerfile
FROM python:3.11-slim-bookworm

# Gereksiz kütüphaneler (libgl1 vb.) kaldırıldı çünkü OCR/OpenCV artık kullanılmıyor.
# Sadece temel sistem güncellemeleri yapılıyor.
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Gereksinimleri kopyala ve yükle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama kodlarını kopyala
COPY . .

# Portu aç
EXPOSE 8000

# Uygulamayı başlat (Shell form kullanarak $PORT değişkeninin çözümlenmesini sağlıyoruz)
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
