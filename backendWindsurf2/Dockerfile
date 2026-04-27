# ExamAI Backend Dockerfile
FROM python:3.11-slim

# Install minimal dependencies for PDF and image processing
# (Tesseract is NOT installed to keep the image slim and deployment simple)
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Default command (will be overridden by Procfile if using Railway/Render)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
