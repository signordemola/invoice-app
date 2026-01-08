"""Email service for sending emails via Resend."""

import base64
from datetime import datetime
import logging
import os
from pathlib import Path
import tempfile
from typing import Any
from jinja2 import Environment, FileSystemLoader, select_autoescape
import resend
from sqlalchemy.orm import Session, joinedload
from app.config.settings import settings
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.services.pdf_service import generate_invoice_pdf
from app.utils.invoice_utils import calculate_invoice_totals

logger = logging.getLogger(__name__)

template_dir = Path(__file__).parent.parent / 'templates' / 'email'
jinja_env = Environment(
    loader=FileSystemLoader(str(template_dir)),
    autoescape=select_autoescape(['html', 'xml']),
    trim_blocks=True,
    lstrip_blocks=True
)


def render_email_template(template_name: str, context: dict) -> str:
    """
    Render email template with context variables.

    Args:
        template_name: Name of template file (e.g., 'invoice_email.html')
        context: Dictionary of variables to pass to template

    Returns:
        Rendered HTML string

    Raises:
        EmailServiceError: If template rendering fails
    """
    try:
        template = jinja_env.get_template(template_name)
        return template.render(**context)
    except Exception as e:
        logger.error(f"Template rendering failed: {str(e)}", exc_info=True)
        raise EmailServiceError(f"Failed to render email template: {str(e)}")


class EmailServiceError(Exception):
    """Base exception for email service errors"""
    pass


class EmailSendError(EmailServiceError):
    """Raised when email fails to send"""
    pass


def send_email(
    to: str,
    subject: str,
    html: str,
    from_address: str | None = None,
    from_name: str | None = None
) -> str:
    """Send a plain email via Resend (no attachments)."""

    return send_email_with_attachment(
        to=to,
        subject=subject,
        html=html,
        attachment_path=None,
        attachment_name=None,
        from_address=from_address,
        from_name=from_name
    )


def send_email_with_attachment(
    to: str,
    subject: str,
    html: str,
    attachment_path: str | None = None,
    attachment_name: str | None = None,
    from_address: str | None = None,
    from_name: str | None = None
) -> str:
    """Send email with optional PDF attachment via Resend."""

    resend.api_key = settings.RESEND_API_KEY

    sender = from_address or settings.EMAIL_FROM_ADDRESS
    sender_name = from_name or settings.EMAIL_FROM_NAME
    from_field = f"{sender_name} <{sender}>"

    try:
        params: dict[str, Any] = {
            "from": from_field,
            "to": [to],
            "subject": subject,
            "html": html,
        }

        if attachment_path:
            file_path = Path(attachment_path)
            file_bytes = file_path.read_bytes()
            filename = attachment_name or file_path.name
            file_base64 = base64.b64encode(file_bytes).decode('utf-8')

            params["attachments"] = [
                {
                    "filename": filename,
                    "content": file_base64
                }
            ]

        response = resend.Emails.send(params)  # type: ignore
        return response["id"]

    except Exception as e:
        raise EmailSendError(f"Failed to send email to {to}: {str(e)}")


def send_invoice_email(invoice_id: int, db: Session) -> str:
    """Send invoice email with PDF attachment to client using Jinja2 template."""

    invoice = db.query(Invoice)\
        .options(joinedload(Invoice.client), joinedload(Invoice.items))\
        .filter(Invoice.id == invoice_id)\
        .first()

    if not invoice:
        raise EmailServiceError(f"Invoice with id {invoice_id} not found")

    # Generate PDF
    pdf_bytes = generate_invoice_pdf(invoice_id, db)

    # Save PDF to temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
        temp_pdf.write(pdf_bytes)
        temp_pdf_path = temp_pdf.name

    try:
        # Calculate invoice totals
        totals = calculate_invoice_totals(invoice)

        # Prepare template context
        context = {
            'company_name': settings.EMAIL_FROM_NAME,
            'company_address': '',  # Add to settings if needed
            'current_year': datetime.now().year,
            'client_name': invoice.client.name,
            'invoice_no': invoice.invoice_no,
            'invoice_date': invoice.date_value.strftime('%B %d, %Y'),
            'due_date': invoice.invoice_due.strftime('%B %d, %Y'),
            'total_amount': f"{totals['vat_total']:,.2f}",
            'currency_symbol': '₦',  # Add to invoice model or settings
        }

        # Render email template (AFTER context is defined)
        html = render_email_template('invoice_email.html', context)

        # Email subject
        subject = f"Invoice {invoice.invoice_no} from {settings.EMAIL_FROM_NAME}"

        # Send email with attachment
        email_id = send_email_with_attachment(
            to=invoice.client.email,
            subject=subject,
            html=html,
            attachment_path=temp_pdf_path,
            attachment_name=f"{invoice.invoice_no}.pdf"
        )

        logger.info(
            f"Invoice email sent using template",
            extra={
                'invoice_id': invoice_id,
                'invoice_no': invoice.invoice_no,
                'email_id': email_id
            }
        )

        return email_id

    finally:
        # Clean up temporary PDF file
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)


def send_payment_confirmation(payment_id: int, db: Session) -> str:
    """Send payment confirmation email to client using Jinja2 template."""

    payment = db.query(Payment)\
        .options(
            joinedload(Payment.invoice).joinedload(Invoice.client),
            joinedload(Payment.invoice).joinedload(Invoice.items),
            joinedload(Payment.invoice).joinedload(Invoice.payments)
    )\
        .filter(Payment.id == payment_id)\
        .first()

    if not payment:
        raise EmailServiceError(f"Payment with id {payment_id} not found")

    # Calculate invoice totals
    totals = calculate_invoice_totals(payment.invoice)

    # Calculate total paid (sum all non-cancelled payments)
    from app.models.payment import PaymentStatus
    total_paid = sum(
        p.amount_paid for p in payment.invoice.payments
        if p.status != PaymentStatus.CANCELLED
    )

    # Calculate remaining balance
    remaining = totals['vat_total'] - total_paid

    # Format payment method for display
    # payment_mode is already a string (native_enum=False), not enum object
    payment_method_display = payment.payment_mode.replace('_', ' ').title()

    # Prepare template context
    context = {
        'company_name': settings.EMAIL_FROM_NAME,
        'current_year': datetime.now().year,
        'client_name': payment.invoice.client.name,
        'amount_paid': f"{payment.amount_paid:,.2f}",
        'payment_date': payment.payment_date.strftime('%B %d, %Y'),
        'payment_method': payment_method_display,
        'invoice_number': payment.invoice.invoice_no,
        'invoice_total': f"{totals['vat_total']:,.2f}",
        'total_paid': f"{total_paid:,.2f}",
        'remaining_balance': f"{remaining:,.2f}",
    }

    # Render email template
    html = render_email_template('payment_confirmation.html', context)

    # Email subject
    subject = f"Payment Confirmation - Invoice {payment.invoice.invoice_no}"

    # Send email
    email_id = send_email(
        to=payment.invoice.client.email,
        subject=subject,
        html=html
    )

    logger.info(
        "Payment confirmation email sent",
        extra={
            'payment_id': payment_id,
            'invoice_id': payment.invoice.id,
            'email_id': email_id,
            'amount': float(payment.amount_paid)
        }
    )

    return email_id


def send_payment_reminder(invoice_id: int, db: Session) -> str:
    """Send payment reminder email for overdue invoice using Jinja2 template."""

    from app.models.invoice import Invoice
    from app.models.payment import PaymentStatus
    from app.utils.datetime_utils import get_current_timezone
    from app.utils.invoice_utils import (
        calculate_invoice_totals,
        calculate_days_overdue,
        is_invoice_overdue
    )

    invoice = db.query(Invoice)\
        .options(
            joinedload(Invoice.client),
            joinedload(Invoice.items),
            joinedload(Invoice.payments)
    )\
        .filter(Invoice.id == invoice_id)\
        .first()

    if not invoice:
        raise EmailServiceError(f"Invoice with id {invoice_id} not found")

    # Get current time (timezone-aware)
    current_time = get_current_timezone("Africa/Lagos")

    # Validate invoice is actually overdue (handles naive/aware comparison)
    if not is_invoice_overdue(invoice.invoice_due, current_time, "Africa/Lagos"):
        raise EmailServiceError(
            f"Invoice {invoice.invoice_no} is not overdue yet. "
            f"Due date: {invoice.invoice_due}, Current: {current_time}"
        )

    # Calculate invoice totals
    totals = calculate_invoice_totals(invoice)

    # Calculate total paid (sum all non-cancelled payments)
    total_paid = sum(
        p.amount_paid for p in invoice.payments
        if p.status != PaymentStatus.CANCELLED
    )

    # Calculate remaining balance
    remaining = totals['vat_total'] - total_paid

    # Calculate days overdue (handles naive/aware comparison)
    days_overdue = calculate_days_overdue(
        invoice.invoice_due,
        current_time,
        "Africa/Lagos"
    )

    # Determine subject line based on urgency
    if days_overdue <= 7:
        subject = f"Friendly Reminder - Invoice {invoice.invoice_no} Due"
    elif days_overdue <= 30:
        subject = f"Payment Reminder - Invoice {invoice.invoice_no} Overdue"
    else:
        subject = f"Urgent: Invoice {invoice.invoice_no} {days_overdue} Days Overdue"

    # Prepare template context
    context = {
        'company_name': settings.EMAIL_FROM_NAME,
        'current_year': datetime.now().year,
        'client_name': invoice.client.name,
        'invoice_number': invoice.invoice_no,
        'invoice_date': invoice.date_value.strftime('%B %d, %Y'),
        'due_date': invoice.invoice_due.strftime('%B %d, %Y'),
        'days_overdue': days_overdue,
        'amount_due': f"{remaining:,.2f}",
    }

    # Render email template
    html = render_email_template('payment_reminder.html', context)

    # Send email
    email_id = send_email(
        to=invoice.client.email,
        subject=subject,
        html=html
    )

    logger.info(
        "Payment reminder sent",
        extra={
            'invoice_id': invoice_id,
            'invoice_no': invoice.invoice_no,
            'email_id': email_id,
            'days_overdue': days_overdue,
            'amount_due': float(remaining)
        }
    )

    return email_id
