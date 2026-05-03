# ExamAI Backend Dockerfile
FROM python:3.11-slim-bookworm

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python -m py_compile \
    main.py \
    routers/notes.py \
    routers/quiz.py \
    services/ai_service.py \
    services/celery_tasks.py \
    services/extraction_service.py \
    utils/security.py

RUN python -c "import os; print('deploy_probe extraction_service_bytes=', os.path.getsize('services/extraction_service.py'))"

EXPOSE 8000

CMD uvicorn main:app --host 0.0.0.0 --port $PORT
