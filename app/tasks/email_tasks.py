import logging

from celery import Task
from celery.exceptions import Reject

from app.config.database import SessionLocal
from app.core.celery_app import celery_app


logger = logging.getLogger(__name__)


def get_task_db_session():
    """
    Create database session for Celery tasks.

    Official pattern: Create new session per task invocation.
    Use context manager to ensure proper cleanup.

    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@celery_app.task(
    bind=True,
    name='email.send_invoice',
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    acks_late=True,
    reject_on_worker_lost=True,
)
def send_invoice_email_task(self: Task, invoice_id: int) -> dict:
    """
    Send invoice email to client.

    Official Celery pattern:
    - Creates DB session per invocation
    - Uses autoretry for transient failures
    - Proper error categorization
    - Structured logging

    Args:
        invoice_id: ID of invoice to send

    Returns:
        Dict with email_id and status

    Raises:
        Reject: On permanent failures (404, validation errors)
    """
    from app.services.email_service import (
        send_invoice_email,
        EmailServiceError,
        EmailSendError
    )

    logger.info(
        "Starting send_invoice_email_task",
        extra={
            "invoice_id": invoice_id,
            "task_id": self.request.id,
            "retry_count": self.request.retries
        }
    )

    # Create DB session using official pattern
    db_gen = get_task_db_session()
    db = next(db_gen)

    try:
        # Call email service
        email_id = send_invoice_email(invoice_id=invoice_id, db=db)

        logger.info(
            "Invoice email sent successfully",
            extra={
                "invoice_id": invoice_id,
                "email_id": email_id,
                "task_id": self.request.id
            }
        )

        return {
            "status": "sent",
            "invoice_id": invoice_id,
            "email_id": email_id,
            "task_id": self.request.id
        }

    except EmailSendError as e:
        # Transient error - let autoretry handle it
        logger.warning(
            f"Email send failed, will retry: {str(e)}",
            extra={
                "invoice_id": invoice_id,
                "task_id": self.request.id,
                "retry_count": self.request.retries
            }
        )
        # Autoretry will handle this due to autoretry_for config
        raise

    except EmailServiceError as e:
        # Permanent error - reject task (don't retry)
        logger.error(
            f"Permanent email error, rejecting task: {str(e)}",
            extra={
                "invoice_id": invoice_id,
                "task_id": self.request.id
            },
            exc_info=True
        )
        # Reject prevents infinite retries on permanent failures
        raise Reject(str(e), requeue=False)

    except Exception as e:
        # Unexpected error - log and let autoretry handle
        logger.error(
            f"Unexpected error in email task: {str(e)}",
            extra={
                "invoice_id": invoice_id,
                "task_id": self.request.id
            },
            exc_info=True
        )
        raise

    finally:
        # Ensure DB session cleanup
        try:
            next(db_gen, None)
        except StopIteration:
            pass


@celery_app.task(
    bind=True,
    name='email.send_payment_confirmation',
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    acks_late=True,
    reject_on_worker_lost=True,
)
def send_payment_confirmation_task(self: Task, payment_id: int) -> dict:
    """
    Send payment confirmation email to client.

    Official Celery pattern for transactional emails with retry logic.

    Args:
        payment_id: ID of payment to confirm

    Returns:
        Dict with email_id and status

    Raises:
        Reject: On permanent failures (payment not found, invalid data)
    """
    from app.services.email_service import (
        send_payment_confirmation,
        EmailServiceError,
        EmailSendError
    )

    logger.info(
        "Starting send_payment_confirmation_task",
        extra={
            "payment_id": payment_id,
            "task_id": self.request.id,
            "retry_count": self.request.retries
        }
    )

    # Create DB session per official pattern
    db_gen = get_task_db_session()
    db = next(db_gen)

    try:
        email_id = send_payment_confirmation(payment_id=payment_id, db=db)

        logger.info(
            "Payment confirmation email sent successfully",
            extra={
                "payment_id": payment_id,
                "email_id": email_id,
                "task_id": self.request.id
            }
        )

        return {
            "status": "sent",
            "payment_id": payment_id,
            "email_id": email_id,
            "task_id": self.request.id
        }

    except EmailSendError as e:
        # Transient error - autoretry handles this
        logger.warning(
            f"Payment email send failed, will retry: {str(e)}",
            extra={
                "payment_id": payment_id,
                "task_id": self.request.id,
                "retry_count": self.request.retries
            }
        )
        raise

    except EmailServiceError as e:
        # Permanent error - reject without retry
        logger.error(
            f"Permanent error sending payment confirmation: {str(e)}",
            extra={
                "payment_id": payment_id,
                "task_id": self.request.id
            },
            exc_info=True
        )
        raise Reject(str(e), requeue=False)

    except Exception as e:
        logger.error(
            f"Unexpected error in payment confirmation task: {str(e)}",
            extra={
                "payment_id": payment_id,
                "task_id": self.request.id
            },
            exc_info=True
        )
        raise

    finally:
        # Cleanup DB session
        try:
            next(db_gen, None)
        except StopIteration:
            pass


@celery_app.task(
    bind=True,
    name='email.send_overdue_reminders',
    time_limit=600,  # 10 minutes max
    soft_time_limit=540,  # 9 minutes soft limit
    acks_late=True,
)
def send_overdue_reminders_task(self: Task) -> dict:
    """
    Scheduled task: Send payment reminders for overdue invoices.

    Runs daily via Celery Beat scheduler. Queries for overdue invoices
    and sends reminder emails respecting reminder_frequency settings.

    Official pattern for batch processing tasks:
    - Processes invoices in batches
    - Tracks success/failure counts
    - Time-limited execution

    Returns:
        Dict with processing statistics
    """
    from datetime import datetime
    from app.models.invoice import Invoice, InvoiceStatus
    from app.services.email_service import (
        send_payment_reminder,
        EmailServiceError
    )
    from app.utils.datetime_utils import get_current_timezone

    logger.info(
        "Starting scheduled overdue reminders task",
        extra={"task_id": self.request.id}
    )

    # Create DB session
    db_gen = get_task_db_session()
    db = next(db_gen)

    stats = {
        "total_overdue": 0,
        "reminders_sent": 0,
        "reminders_skipped": 0,
        "reminders_failed": 0,
        "errors": []
    }

    try:
        current_time = get_current_timezone("Africa/Lagos")

        # Query overdue invoices that have reminders enabled
        overdue_invoices = db.query(Invoice).filter(
            Invoice.status == InvoiceStatus.OVERDUE,
            Invoice.send_reminders == True,
            Invoice.reminder_frequency.isnot(None)
        ).all()

        stats["total_overdue"] = len(overdue_invoices)

        logger.info(
            f"Found {stats['total_overdue']} overdue invoices with reminders enabled"
        )

        for invoice in overdue_invoices:
            try:
                # Type safety: reminder_frequency already filtered for not None
                reminder_frequency = invoice.reminder_frequency
                if reminder_frequency is None:
                    # Skip if somehow None (defensive programming)
                    stats["reminders_skipped"] += 1
                    continue

                # Check if reminder should be sent based on frequency
                should_send = False

                # Type safety: Check reminder_logs structure
                if not invoice.reminder_logs:
                    # Never sent before - send now
                    should_send = True
                else:
                    last_sent_str = invoice.reminder_logs.get('last_sent')

                    if last_sent_str is None:
                        # No last_sent recorded - send now
                        should_send = True
                    else:
                        # Type safety: last_sent_str is definitely str here
                        try:
                            last_sent = datetime.fromisoformat(last_sent_str)
                            days_since_last = (current_time - last_sent).days

                            # Type safety: reminder_frequency is int here
                            if days_since_last >= reminder_frequency:
                                should_send = True
                        except (ValueError, TypeError) as e:
                            # Invalid date format - log and send anyway
                            logger.warning(
                                f"Invalid last_sent date for invoice {invoice.id}: {str(e)}"
                            )
                            should_send = True

                if should_send:
                    # Send reminder email
                    email_id = send_payment_reminder(
                        invoice_id=invoice.id,
                        db=db
                    )

                    # Update reminder logs
                    if not invoice.reminder_logs:
                        invoice.reminder_logs = {}

                    invoice.reminder_logs['last_sent'] = current_time.isoformat(
                    )
                    invoice.reminder_logs['count'] = invoice.reminder_logs.get(
                        'count', 0) + 1

                    db.commit()

                    stats["reminders_sent"] += 1

                    logger.info(
                        f"Reminder sent for invoice {invoice.invoice_no}",
                        extra={
                            "invoice_id": invoice.id,
                            "email_id": email_id
                        }
                    )
                else:
                    stats["reminders_skipped"] += 1
                    logger.debug(
                        f"Skipping reminder for invoice {invoice.invoice_no} - frequency not met"
                    )

            except EmailServiceError as e:
                stats["reminders_failed"] += 1
                stats["errors"].append({
                    "invoice_id": invoice.id,
                    "error": str(e)
                })
                logger.error(
                    f"Failed to send reminder for invoice {invoice.id}: {str(e)}",
                    exc_info=True
                )
                # Continue with next invoice
                continue

        logger.info(
            "Overdue reminders task completed",
            extra={
                "task_id": self.request.id,
                "stats": stats
            }
        )

        return stats

    except Exception as e:
        logger.error(
            f"Critical error in overdue reminders task: {str(e)}",
            extra={"task_id": self.request.id},
            exc_info=True
        )
        raise

    finally:
        # Cleanup DB session
        try:
            next(db_gen, None)
        except StopIteration:
            pass
