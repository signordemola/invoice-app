from datetime import datetime
from decimal import Decimal
from math import ceil
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.client import Client
from app.models.invoice import Invoice
from app.models.item import Item
from app.schemas.invoice import InvoiceCreate, InvoiceUpdate
from app.utils.datetime_utils import get_current_timezone
from app.utils.invoice_utils import InvoiceTotals, calculate_due_date, calculate_invoice_totals, generate_invoice_number, track_invoice_view


class InvoiceServiceError(Exception):
    """Base exception for invoice service errors"""
    pass


class InvoiceNotFoundError(InvoiceServiceError):
    """Raised when an invoice is not found"""
    pass


class InvoiceNumberExistsError(InvoiceServiceError):
    """Raised when attempting to use a duplicate invoice number"""
    pass


class InvalidInvoiceDataError(InvoiceServiceError):
    """Raised when invoice data is invalid (e.g., future dates, negative amounts)"""
    pass


class ClientNotFoundError(InvoiceServiceError):
    """Raised when the specified client doesn't exist"""
    pass


def create_invoice(invoice_data: InvoiceCreate, db: Session, payment_terms_days: int = 30,  auto_generate_pdf: bool = False,
                   auto_send_email: bool = False) -> Invoice:
    """Create a new invoice with automation triggers."""

    client = db.query(Client).filter(
        Client.id == invoice_data.client_id).first()
    if not client:
        raise ClientNotFoundError(
            f"Client with id {invoice_data.client_id} not found!")

    invoice_dict = invoice_data.model_dump(exclude={"items"})
    invoice = Invoice(**invoice_dict)

    current_date = get_current_timezone("Africa/Lagos")
    invoice.invoice_due = calculate_due_date(current_date, payment_terms_days)

    db.add(invoice)
    db.flush()

    invoice.invoice_no = generate_invoice_number(invoice.id)
    invoice.purchase_no = invoice.id

    for item_data in invoice_data.items:
        qty = Decimal(item_data.qty)
        rate = item_data.rate
        amount = (qty * rate).quantize(Decimal('0.01'))

        item = Item(
            item_desc=item_data.item_desc,
            qty=qty,
            rate=rate,
            amount=amount,
            invoice_id=invoice.id
        )
        db.add(item)

    db.commit()
    db.refresh(invoice)

    if auto_generate_pdf:
        print('Generating PDF for invoice...')
        pass

    if auto_send_email:
        print('Sending invoice email to client...')
        pass

    if invoice.send_reminders and invoice.reminder_frequency:
        print('Scheduling reminders for invoice...')
        pass

    return invoice


def get_invoice_by_id(
    invoice_id: int,
    db: Session,
    track_view: bool = True,
    load_relationships: bool = True
) -> tuple[Invoice, InvoiceTotals]:
    """Get a single invoice by ID with optional view tracking."""

    query = db.query(Invoice)

    if load_relationships:
        query = query.options(
            joinedload(Invoice.client),
            selectinload(Invoice.items),
            selectinload(Invoice.payments)
        )

    invoice = query.filter(Invoice.id == invoice_id).first()

    if not invoice:
        raise InvoiceNotFoundError(f"Invoice with id {invoice_id} not found!")

    if track_view:
        track_invoice_view(invoice)
        db.commit()

    totals = calculate_invoice_totals(invoice)

    return invoice, totals


def get_invoices_paginated(
    db: Session,
    page: int = 1,
    limit: int = 10,
    search: str | None = None
) -> dict:
    """Get paginated list of invoices with optional search."""

    if limit < 1 or limit > 100:
        raise ValueError("Limit must be between 1 and 100")

    query = db.query(Invoice)\
        .join(Client, Client.id == Invoice.client_id)\
        .options(
            joinedload(Invoice.client),
            selectinload(Invoice.items),
            selectinload(Invoice.payments)
    )

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                func.lower(Client.name).like(func.lower(search_term)),
                func.lower(Client.email).like(func.lower(search_term))
            )
        )

    total = query.count()

    skip = (page - 1) * limit
    invoices = query\
        .order_by(Invoice.id.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()

    total_pages = ceil(total / limit) if total > 0 else 0

    return {
        "invoices": invoices,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages
        }
    }


def update_invoice(
    invoice_id: int,
    invoice_data: InvoiceUpdate,
    db: Session
) -> Invoice:
    """Update an existing invoice (partial update)."""

    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()

    if not invoice:
        raise InvoiceNotFoundError(f"Invoice with id {invoice_id} not found")

    update_data = invoice_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(invoice, field, value)

    db.commit()
    db.refresh(invoice)

    return invoice


def delete_invoice(
    invoice_id: int,
    db: Session,
    allow_with_payments: bool = True
) -> None:
    """Delete an invoice and all related data (items, payments)"""

    invoice = db.query(Invoice)\
        .options(selectinload(Invoice.payments))\
        .filter(Invoice.id == invoice_id)\
        .first()

    if not invoice:
        raise InvoiceNotFoundError(f"Invoice with id {invoice_id} not found!")

    if not allow_with_payments and invoice.payments:
        raise InvalidInvoiceDataError(
            f"Cannot delete invoice {invoice_id} because it has {len(invoice.payments)} payment(s). "
            "This protects financial records from accidental deletion."
        )

    db.delete(invoice)
    db.commit()
