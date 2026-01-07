"""Celery configuration for background tasks."""

from celery import Celery

from app.config import settings

celery_app = Celery(
    "invoice_app",
    broker=settings.UPSTASH_REDIS_BROKER_URL,
    backend=settings.UPSTASH_REDIS_BACKEND_URL or settings.UPSTASH_REDIS_BROKER_URL,
    include=['app.tasks.invoice_tasks',
             'app.tasks.email_tasks', 'app.tasks.payment_tasks']
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Africa/Lagos',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    task_soft_time_limit=240,
    worker_prefetch_multiplier=1,
)


celery_app.conf.task_default_retry_delay = 60
celery_app.conf.task_max_retries = 5
