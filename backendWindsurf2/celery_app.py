"""
celery_app.py – Celery application configuration.
"""

import logging
import os
from celery import Celery

from config import settings

logger = logging.getLogger(__name__)

# Configure Celery
celery_app = Celery(
    "examai",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["services.celery_tasks"]
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
    },
    task_default_queue="default",
    task_default_exchange="default",
    task_default_exchange_type="direct",
    task_default_routing_key="default",
)

# Configure logging for Celery
celery_app.conf.worker_log_format = "[%(asctime)s: %(levelname)s/%(processName)s] %(message)s"
celery_app.conf.worker_task_log_format = "[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s"

# Set environment variables for Celery
os.environ.setdefault("FORKED_BY_MULTIPROCESSING", "1")

logger.info("Celery application configured successfully")
