@echo off
title ExamAI Backend Start
echo ==============================================
echo        ExamAI Backend Baslatiliyor...
echo ==============================================

:: Virtual Environment kontrolu
if not exist ".venv\Scripts\activate.bat" (
    echo [HATA] .venv klasoru bulunamadi! Lutfen once bagimliliklari yukleyin.
    pause
    exit /b
)

:: Redis servisi uyarısı
echo [BILGI] Redis'in (Docker veya Windows servis) calistigindan emin olun.
echo.

:: Celery Worker'i ayri bir konsol penceresinde baslat
echo [1/2] Celery Worker baslatiliyor...
:: Windows'ta Celery'nin stabil calismasi icin --pool=solo veya gevent tavsiye edilir.
start "ExamAI - Celery Worker" cmd /c "call .venv\Scripts\activate && celery -A celery_app worker --loglevel=info --pool=solo"

:: Uvicorn (FastAPI) ayni pencerede baslatiliyor
echo [2/2] FastAPI Sunucusu (Uvicorn) baslatiliyor...
call .venv\Scripts\activate
uvicorn main:app --reload --port 8000

pause
