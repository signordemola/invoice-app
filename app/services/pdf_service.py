import os

from jinja2 import Environment, FileSystemLoader
from app.utils.invoice_utils import calculate_invoice_totals
from app.models.invoice import Invoice
from xhtml2pdf import pisa
from io import BytesIO
from sqlalchemy.orm import Session, joinedload

template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates/pdf')
jinja_env = Environment(loader=FileSystemLoader(template_dir))


class PDFServiceError(Exception):
    """Base exception for PDF service errors"""
    pass


class PDFInvoiceNotFoundError(PDFServiceError):
    """Raised when invoice doesn't exist for PDF generation"""
    pass


def generate_invoice_pdf(invoice_id: int, db: Session) -> bytes:
    """Generate a PDF for an invoice"""

    invoice = db.query(Invoice)\
        .options(
            joinedload(Invoice.client),
            joinedload(Invoice.items)
    )\
        .filter(Invoice.id == invoice_id)\
        .first()

    if not invoice:
        raise PDFInvoiceNotFoundError(
            f"Invoice with id {invoice_id} not found!")

    total = calculate_invoice_totals(invoice)

    issue_date = invoice.date_value.strftime("%d %B %Y")
    due_date = invoice.invoice_due.strftime("%d %B %Y")

    template = jinja_env.get_template('invoice.html')

    html_content = template.render(
        invoice=invoice,
        issue_date=issue_date,
        due_date=due_date,
        total=total
    )

    buffer = BytesIO()
    result = pisa.CreatePDF(html_content, dest=buffer)

    if result.err:  # type: ignore
        raise PDFServiceError("PDF generation failed")

    buffer.seek(0)
    return buffer.getvalue()
