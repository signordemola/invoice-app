from io import BytesIO
from turtle import width
from sqlalchemy.orm import Session, joinedload

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

from app.models.invoice import Invoice
from app.utils.invoice_utils import calculate_invoice_totals


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
        raise PDFInvoiceNotFoundError(f"Invoice with id {invoice_id} not found!")

    total = calculate_invoice_totals(invoice)

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    right_margin = 50
    y_position = height - 80

    pdf.setFont("Helvetica-Bold", 24)
    title_text = "INVOICE"
    title_width = pdf.stringWidth(title_text, "Helvetica-Bold", 24)
    pdf.drawString(width - title_width - right_margin, y_position, title_text)

    y_position -= 40

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(width - 200, y_position, "Invoice Number:")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(width - 200 + 110, y_position, invoice.invoice_no or "N/A")

    y_position -= 25

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(width - 200, y_position, "Issue Date:")
    pdf.setFont("Helvetica", 12)
    issue_date_str = invoice.date_value.strftime("%d %B %Y")
    pdf.drawString(width - 200 + 110, y_position, issue_date_str)

    y_position -= 25

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(width - 200, y_position, "Due Date:")
    pdf.setFont("Helvetica", 12)
    due_date_str = invoice.invoice_due.strftime("%d %B %Y")
    pdf.drawString(width - 200 + 110, y_position, due_date_str)

    y_position -= 25

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(width - 200, y_position, "Status:")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(width - 200 + 110, y_position, invoice.status.upper())

    y_position = height - 80

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y_position, "Bill To:")

    y_position -= 20
    pdf.setFont("Helvetica", 11)
    pdf.drawString(50, y_position, invoice.client.name)

    y_position -= 18
    pdf.setFont("Helvetica", 10)
    pdf.drawString(50, y_position, invoice.client.email)

    y_position = height - 200

    col_desc = 50
    col_qty = 350
    col_rate = 420
    col_amount = 500

    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(col_desc, y_position, "Description")
    pdf.drawString(col_qty, y_position, "Qty")
    pdf.drawString(col_rate, y_position, "Rate")
    pdf.drawString(col_amount, y_position, "Amount")

    y_position -= 5
    pdf.line(50, y_position, width - 50, y_position)
    y_position -= 20

    pdf.setFont("Helvetica", 10)
    for item in invoice.items:
        pdf.drawString(col_desc, y_position, item.item_desc[:50])
        pdf.drawString(col_qty, y_position, str(item.qty))
        pdf.drawString(col_rate, y_position, f"{item.rate:.2f}")
        pdf.drawString(col_amount, y_position, f"{item.amount:.2f}")
        y_position -= 20

    y_position -= 30

    totals_label_x = width - 200
    totals_amount_x = width - 50

    pdf.setFont("Helvetica", 10)

    pdf.drawString(totals_label_x, y_position, "Subtotal:")
    pdf.drawRightString(totals_amount_x, y_position,
                        f"{total['subtotal']:.2f}")
    y_position -= 20

    pdf.drawString(totals_label_x, y_position, "Discount:")
    pdf.drawRightString(totals_amount_x, y_position,
                        f"{total['discount']:.2f}")
    y_position -= 20

    pdf.drawString(totals_label_x, y_position, "Total:")
    pdf.drawRightString(totals_amount_x, y_position, f"{total['total']:.2f}")
    y_position -= 20

    pdf.drawString(totals_label_x, y_position, "VAT (7.5%):")
    pdf.drawRightString(totals_amount_x, y_position, f"{total['vat']:.2f}")
    y_position -= 20

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(totals_label_x, y_position, "Grand Total:")
    pdf.drawRightString(totals_amount_x, y_position,
                        f"{total['vat_total']:.2f}")

    pdf.showPage()
    pdf.save()

    buffer.seek(0)
    return buffer.getvalue()
