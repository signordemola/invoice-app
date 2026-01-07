"""Email service for sending emails via Resend."""

import base64
from datetime import datetime
import logging
import os
from pathlib import Path
import tempfile
from typing import Any
import resend
from sqlalchemy.orm import Session, joinedload
from app.config.settings import settings
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.services.pdf_service import generate_invoice_pdf
from app.utils.invoice_utils import calculate_invoice_totals

logger = logging.getLogger(__name__)


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
    """Send invoice email with PDF attachment to client."""

    invoice = db.query(Invoice)\
        .options(joinedload(Invoice.client), joinedload(Invoice.items))\
        .filter(Invoice.id == invoice_id)\
        .first()

    if not invoice:
        raise EmailServiceError(f"Invoice with id {invoice_id} not found")

    pdf_bytes = generate_invoice_pdf(invoice_id, db)

    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
        temp_pdf.write(pdf_bytes)
        temp_pdf_path = temp_pdf.name

    try:
        totals = calculate_invoice_totals(invoice)

        subject = f"Invoice {invoice.invoice_no} from {settings.EMAIL_FROM_NAME}"

        html = f"""
        <html>
            <body>
                <p>Dear {invoice.client.name},</p>
                <p>Please find attached invoice {invoice.invoice_no} for {totals['vat_total']}.</p>
                <p>Due date: {invoice.invoice_due.strftime('%B %d, %Y')}</p>
                <p>Thank you for your business!</p>
            </body>
        </html>
        """

        email_id = send_email_with_attachment(
            to=invoice.client.email,
            subject=subject,
            html=html,
            attachment_path=temp_pdf_path,
            attachment_name=f"{invoice.invoice_no}.pdf"
        )

        return email_id

    finally:
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)


def send_payment_confirmation(payment_id: int, db: Session) -> str:
    """Send payment confirmation email to client."""

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

    totals = calculate_invoice_totals(payment.invoice)
    total_paid = sum(p.amount_paid for p in payment.invoice.payments)
    remaining = totals['vat_total'] - total_paid

    subject = f"Payment Confirmation - Invoice {payment.invoice.invoice_no}"

    html = f"""
    <html>
        <body>
            <p>Dear {payment.invoice.client.name},</p>
            <p>We confirm receipt of your payment of {payment.amount_paid} for invoice {payment.invoice.invoice_no}.</p>
            <p><strong>Payment Details:</strong></p>
            <ul>
                <li>Amount Paid: {payment.amount_paid}</li>
                <li>Payment Date: {payment.payment_date.strftime('%B %d, %Y')}</li>
                <li>Payment Method: {payment.payment_mode.replace('_', ' ').title()}</li>
            </ul>
            <p><strong>Invoice Balance:</strong></p>
            <ul>
                <li>Invoice Total: {totals['vat_total']}</li>
                <li>Total Paid: {total_paid}</li>
                <li>Remaining Balance: {remaining}</li>
            </ul>
            <p>Thank you for your payment!</p>
        </body>
    </html>
    """

    # Send to invoice's client
    email_id = send_email(
        to=payment.invoice.client.email,
        subject=subject,
        html=html
    )

    return email_id


def send_payment_reminder(invoice_id: int, db: Session) -> str:
    """Send payment reminder email for overdue invoice."""

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

    totals = calculate_invoice_totals(invoice)
    total_paid = sum(p.amount_paid for p in invoice.payments)
    remaining = totals['vat_total'] - total_paid

    days_overdue = (datetime.now() - invoice.invoice_due).days

    if days_overdue <= 7:
        subject = f"Friendly Reminder - Invoice {invoice.invoice_no} Due"
    elif days_overdue <= 30:
        subject = f"Payment Reminder - Invoice {invoice.invoice_no} Overdue"
    else:
        subject = f"Urgent: Invoice {invoice.invoice_no} {days_overdue} Days Overdue"

    html = f"""
    <html>
        <body>
            <p>Dear {invoice.client.name},</p>
            <p>This is a reminder that invoice {invoice.invoice_no} is now <strong>{days_overdue} days overdue</strong>.</p>
            <p><strong>Invoice Details:</strong></p>
            <ul>
                <li>Invoice Number: {invoice.invoice_no}</li>
                <li>Original Due Date: {invoice.invoice_due.strftime('%B %d, %Y')}</li>
                <li>Amount Due: {remaining}</li>
            </ul>
            <p>Please remit payment at your earliest convenience.</p>
            <p>If you have already sent payment, please disregard this notice.</p>
            <p>Thank you for your attention to this matter.</p>
        </body>
    </html>
    """

    email_id = send_email(
        to=invoice.client.email,
        subject=subject,
        html=html
    )

    return email_id
