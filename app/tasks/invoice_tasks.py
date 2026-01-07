"""Invoice background tasks following Celery 5.6.0 official patterns.

Handles PDF generation and other invoice-related async operations.
"""

import logging
from celery import Task
from celery.exceptions import Reject

from app.core.celery_app import celery_app
from app.config.database import SessionLocal

logger = logging.getLogger(__name__)


def get_task_db_session():
    """
    Create database session for Celery tasks.

    Official pattern: Create new session per task invocation.

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
    name='invoice.generate_pdf',
    max_retries=2,
    default_retry_delay=120,  # 2 minutes between retries
    time_limit=300,  # 5 minutes hard limit (PDF generation can be slow)
    soft_time_limit=240,  # 4 minutes soft limit
    acks_late=True,
    reject_on_worker_lost=True,
)
def generate_invoice_pdf_task(self: Task, invoice_id: int) -> dict:
    """
    Generate PDF for an invoice asynchronously.

    CPU-intensive task with longer time limits. Does not use autoretry
    because PDF generation is expensive and failures are usually permanent
    (missing data, template errors).

    Args:
        invoice_id: ID of invoice to generate PDF for

    Returns:
        Dict with pdf_generated status and file info

    Raises:
        Reject: On permanent failures (invoice not found, template error)
    """
    from app.services.pdf_service import (
        generate_invoice_pdf,
        PDFServiceError,
        PDFInvoiceNotFoundError
    )

    logger.info(
        "Starting generate_invoice_pdf_task",
        extra={
            "invoice_id": invoice_id,
            "task_id": self.request.id,
            "retry_count": self.request.retries
        }
    )

    # Create DB session
    db_gen = get_task_db_session()
    db = next(db_gen)

    try:
        # Generate PDF (returns bytes)
        pdf_bytes = generate_invoice_pdf(invoice_id=invoice_id, db=db)

        # Get invoice info for filename
        from app.models.invoice import Invoice
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()

        if not invoice:
            raise PDFInvoiceNotFoundError(f"Invoice {invoice_id} not found")

        filename = f"{invoice.invoice_no}.pdf" if invoice.invoice_no else f"invoice_{invoice_id}.pdf"

        logger.info(
            "Invoice PDF generated successfully",
            extra={
                "invoice_id": invoice_id,
                "filename": filename,
                "size_bytes": len(pdf_bytes),
                "task_id": self.request.id
            }
        )

        return {
            "status": "generated",
            "invoice_id": invoice_id,
            "filename": filename,
            "size_bytes": len(pdf_bytes),
            "task_id": self.request.id
        }

    except PDFInvoiceNotFoundError as e:
        # Permanent error - invoice doesn't exist
        logger.error(
            f"Invoice not found for PDF generation: {str(e)}",
            extra={
                "invoice_id": invoice_id,
                "task_id": self.request.id
            },
            exc_info=True
        )
        raise Reject(str(e), requeue=False)

    except PDFServiceError as e:
        # Permanent error - template or rendering issue
        logger.error(
            f"PDF generation service error: {str(e)}",
            extra={
                "invoice_id": invoice_id,
                "task_id": self.request.id
            },
            exc_info=True
        )
        raise Reject(str(e), requeue=False)

    except Exception as e:
        # Unexpected error - retry with backoff
        logger.error(
            f"Unexpected error generating PDF: {str(e)}",
            extra={
                "invoice_id": invoice_id,
                "task_id": self.request.id,
                "retry_count": self.request.retries
            },
            exc_info=True
        )

        # Manual retry with longer delay for resource-intensive tasks
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=120)
        else:
            # Max retries reached
            raise

    finally:
        # Cleanup DB session
        try:
            next(db_gen, None)
        except StopIteration:
            pass


@celery_app.task(
    bind=True,
    name='invoice.generate_and_send',
    max_retries=1,
    default_retry_delay=300,  # 5 minutes
    time_limit=600,  # 10 minutes total (PDF + email)
    soft_time_limit=540,
    acks_late=True,
    reject_on_worker_lost=True,
)
def generate_and_send_invoice_task(self: Task, invoice_id: int) -> dict:
    """
    Composite task: Generate PDF and send invoice email.

    Orchestrates two operations sequentially:
    1. Generate invoice PDF
    2. Send invoice email with PDF attachment

    This is a coordinating task that calls other tasks synchronously.
    For async chaining, use Celery chains in the API layer instead.

    Args:
        invoice_id: ID of invoice to process

    Returns:
        Dict with both PDF generation and email sending results

    Raises:
        Reject: On permanent failures in either step
    """
    from app.services.pdf_service import (
        generate_invoice_pdf,
        PDFServiceError,
        PDFInvoiceNotFoundError
    )
    from app.services.email_service import (
        send_invoice_email,
        EmailServiceError,
        EmailSendError
    )

    logger.info(
        "Starting generate_and_send_invoice_task",
        extra={
            "invoice_id": invoice_id,
            "task_id": self.request.id
        }
    )

    # Create DB session
    db_gen = get_task_db_session()
    db = next(db_gen)

    results = {
        "invoice_id": invoice_id,
        "pdf_generated": False,
        "email_sent": False,
        "pdf_info": None,
        "email_info": None,
        "task_id": self.request.id
    }

    try:
        # Step 1: Generate PDF
        logger.info(f"Step 1/2: Generating PDF for invoice {invoice_id}")

        try:
            pdf_bytes = generate_invoice_pdf(invoice_id=invoice_id, db=db)

            from app.models.invoice import Invoice
            invoice = db.query(Invoice).filter(
                Invoice.id == invoice_id).first()

            if not invoice:
                raise PDFInvoiceNotFoundError(
                    f"Invoice {invoice_id} not found")

            filename = f"{invoice.invoice_no}.pdf" if invoice.invoice_no else f"invoice_{invoice_id}.pdf"

            results["pdf_generated"] = True
            results["pdf_info"] = {
                "filename": filename,
                "size_bytes": len(pdf_bytes)
            }

            logger.info(
                f"PDF generated successfully: {filename}",
                extra={
                    "invoice_id": invoice_id,
                    "size_bytes": len(pdf_bytes)
                }
            )

        except (PDFInvoiceNotFoundError, PDFServiceError) as e:
            logger.error(
                f"PDF generation failed permanently: {str(e)}",
                extra={"invoice_id": invoice_id},
                exc_info=True
            )
            raise Reject(f"PDF generation failed: {str(e)}", requeue=False)

        # Step 2: Send Email
        logger.info(
            f"Step 2/2: Sending invoice email for invoice {invoice_id}")

        try:
            email_id = send_invoice_email(invoice_id=invoice_id, db=db)

            results["email_sent"] = True
            results["email_info"] = {
                "email_id": email_id
            }

            logger.info(
                f"Invoice email sent successfully: {email_id}",
                extra={
                    "invoice_id": invoice_id,
                    "email_id": email_id
                }
            )

        except EmailSendError as e:
            # Email failed but PDF succeeded - log warning, don't fail task
            logger.warning(
                f"Email sending failed (PDF was generated): {str(e)}",
                extra={"invoice_id": invoice_id},
                exc_info=True
            )
            results["email_sent"] = False
            results["email_info"] = {
                "error": str(e)
            }
            # Don't raise - PDF generation succeeded, partial success is OK

        except EmailServiceError as e:
            # Permanent email error
            logger.error(
                f"Email service error (PDF was generated): {str(e)}",
                extra={"invoice_id": invoice_id},
                exc_info=True
            )
            results["email_sent"] = False
            results["email_info"] = {
                "error": str(e)
            }
            # Don't raise - partial success is acceptable

        logger.info(
            "generate_and_send_invoice_task completed",
            extra={
                "invoice_id": invoice_id,
                "results": results
            }
        )

        return results

    except Reject:
        # Re-raise Reject exceptions
        raise

    except Exception as e:
        logger.error(
            f"Unexpected error in composite task: {str(e)}",
            extra={
                "invoice_id": invoice_id,
                "task_id": self.request.id
            },
            exc_info=True
        )

        # Retry the entire composite task
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=300)
        else:
            raise

    finally:
        # Cleanup DB session
        try:
            next(db_gen, None)
        except StopIteration:
            pass
