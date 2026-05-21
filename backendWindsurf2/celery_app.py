"""
celery_app.py – Celery application configuration.
"""

import logging
import os
from celery import Celery

from config import settings

logger = logging.getLogger(__name__)

# Ensure REDIS_URL has required parameters for SSL if using rediss://
redis_url = settings.REDIS_URL
if redis_url.startswith("rediss://") and "ssl_cert_reqs" not in redis_url:
    # Append the parameter to the URL
    separator = "&" if "?" in redis_url else "?"
    redis_url = f"{redis_url}{separator}ssl_cert_reqs=none"
    logger.info("Modified REDIS_URL for SSL compatibility")

# CRITICAL: Disable uvloop for Celery worker to avoid asyncio.run() conflicts
if os.environ.get("FORKED_BY_MULTIPROCESSING") == "1":
    try:
        import asyncio
        # Try to prevent uvloop from taking over if it's installed
        try:
            import uvloop
            asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
            logger.info("Disabled uvloop policy for Celery worker")
        except ImportError:
            pass
    except Exception as e:
        logger.warning(f"Could not adjust event loop policy: {e}")

# Configure Celery
celery_app = Celery(
    "examai",
    broker=redis_url,
    backend=redis_url,
    include=["services.celery_tasks"]  # refresh_gemini_models_task burada tanımlı
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    result_expires=3600,  # 1 hour
    task_routes={
        "services.celery_tasks.generate_quiz_task": {"queue": "quiz_generation"},
        "services.celery_tasks.grade_quiz_task": {"queue": "default"},
        "services.celery_tasks.refresh_gemini_models_task": {"queue": "default"},
    },
    task_default_queue="default",
    task_default_exchange="default",
    task_default_exchange_type="direct",
    task_default_routing_key="default",
    # ── Celery Beat: Zamanlanmış Görevler ─────────────────────────────────────
    beat_schedule={
        "refresh-gemini-models-daily": {
            "task": "services.celery_tasks.refresh_gemini_models_task",
            "schedule": 86400,  # Her 24 saatte bir (saniye cinsinden)
            # Belirli saat için: crontab(hour=3, minute=0)
            # from celery.schedules import crontab
        },
    },
)

# Configure logging for Celery
celery_app.conf.worker_log_format = "[%(asctime)s: %(levelname)s/%(processName)s] %(message)s"
celery_app.conf.worker_task_log_format = "[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s"

# Set environment variables for Celery
os.environ.setdefault("FORKED_BY_MULTIPROCESSING", "1")

logger.info("Celery application configured successfully")
