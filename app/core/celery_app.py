"""Celery configuration for background tasks."""

from celery import Celery
from celery.schedules import crontab
from app.config import settings


def configure_redis_ssl_url(url: str) -> str:
    """
    Add SSL certificate requirements to rediss:// URLs.

    Celery with Redis SSL requires explicit ssl_cert_reqs parameter.
    See: https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/redis.html

    Args:
        url: Redis URL (redis:// or rediss://)

    Returns:
        URL with SSL parameters if using rediss://
    """
    if url.startswith('rediss://'):
        separator = '&' if '?' in url else '?'
        return f'{url}{separator}ssl_cert_reqs=required'
    return url


# Validate broker URL exists (required for Celery)
if not settings.UPSTASH_REDIS_BROKER_URL:
    raise ValueError(
        "UPSTASH_REDIS_BROKER_URL must be set in environment variables. "
        "Celery cannot start without a broker URL."
    )

# Configure broker with SSL if needed
broker_url = configure_redis_ssl_url(settings.UPSTASH_REDIS_BROKER_URL)

# Configure backend (can be None for fire-and-forget tasks)
backend_url = None
if settings.UPSTASH_REDIS_BACKEND_URL:
    backend_url = configure_redis_ssl_url(settings.UPSTASH_REDIS_BACKEND_URL)

# Create Celery instance (official pattern from docs)
celery_app = Celery(
    "invoice_app",
    broker=broker_url,
    backend=backend_url,
)

# Configuration via conf.update() (official pattern)
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
    worker_max_tasks_per_child=1000,
    result_expires=3600,
    imports=[
        'app.tasks.email_tasks',
        'app.tasks.invoice_tasks',
    ],
    beat_schedule={
        'send-overdue-reminders-daily': {
            'task': 'email.send_overdue_reminders',
            'schedule': crontab(hour=9, minute=0),
            'options': {
                'expires': 3600,
            }
        },
    }
)
