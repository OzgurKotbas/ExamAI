@echo off
title ExamAI All-In-One Launcher
echo ==============================================
echo        ExamAI Tum Servisler Baslatiliyor
echo ==============================================

:: Betigin calistigi klasore (Ana Kok) git
cd /d "%~dp0"

echo [0/4] Docker Durumu Kontrol Ediliyor...
docker info >nul 2>&1
if %errorlevel% == 0 (
    echo Docker zaten calisiyor.
    goto docker_ready
)

echo Docker calismiyor. Baslatiliyor...
:: Microsoft Windows'ta varsayilan Docker Desktop yolu
start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
echo Docker'in acilmasi bekleniyor (bu biraz zaman alabilir)...

:wait_docker
timeout /t 5 /nobreak >nul
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo Docker hala hazir degil, bekleniyor...
    goto wait_docker
)
echo Docker basariyla baslatildi ve hazir!

:docker_ready
echo.

echo [1/4] Altyapi (PostgreSQL ve Redis) Baslatiliyor...
echo Bilgi: Ilk kurulumda imajlarin indirilmesi biraz vakit alabilir...
docker compose -f backendWindsurf2\docker-compose-infra.yml up -d 2>nul
if %errorlevel% neq 0 (
    docker-compose -f backendWindsurf2\docker-compose-infra.yml up -d
)
echo Veritabanlarinin hazir olmasi icin 5 saniye bekleniyor...
timeout /t 5 /nobreak >nul

echo [2/4] Backend (FastAPI) Baslatiliyor...
start /min "ExamAI - Backend (Uvicorn)" cmd /c "cd backendWindsurf2 && .venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000"

echo [3/5] AI Celery Worker Baslatiliyor...
start /min "ExamAI - AI Worker (Celery)" cmd /c "cd backendWindsurf2 && .venv\Scripts\python.exe -m celery -A celery_app:celery_app worker -Q default,quiz_generation --loglevel=info --pool=solo"

echo [4/5] Celery Beat (Zamanli Gorevler) Baslatiliyor...
start /min "ExamAI - Celery Beat" cmd /c "cd backendWindsurf2 && .venv\Scripts\python.exe -m celery -A celery_app:celery_app beat --loglevel=info"

echo [5/5] Frontend (React/Vite) Baslatiliyor...
start /min "ExamAI - Frontend" cmd /c "cd examai-frontend && npm run dev"

echo.
echo Servislerin uyanmasi icin 5 saniye bekleniyor...
timeout /t 5 /nobreak >nul

echo Tarayici siteyle aciliyor...
start http://localhost:5173

echo.
echo ==============================================
echo Tum sistemler basariyla tetiklendi!
echo ExamAI'niza host edilen 3 siyah konsol penceresini 
echo kapatmadiginiz surece sistem canli kalacaktir.
echo Iyi calismalar!
echo ==============================================
pause
