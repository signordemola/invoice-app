

import logging

from app.core.celery_app import celery_app


logger = logging.getLogger(__name__)


@celery_app.task(
    name='app.tasks.email_tasks.send_invoice_email_task',
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_invoice_email_task() -> None:
    return None


@celery_app.task(
    name='app.tasks.email_tasks.send_payment_confirmation_task',
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_payment_confirmation_task() -> None:
    return None


@celery_app.task(
    name='app.tasks.email_tasks.send_payment_reminder_task',
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_payment_reminder_task() -> None:
    return None
