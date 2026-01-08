from decimal import Decimal
import logging
from math import ceil
from typing import Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.exceptions import ConflictException, NotFoundException, ValidationException
from app.models.client import Client
from app.models.invoice import Invoice, InvoiceStatus
from app.models.item import Item
from app.schemas.invoice import InvoiceCreate, InvoiceUpdate
from app.services.database import transaction_scope
from app.utils.datetime_utils import get_current_timezone
from app.utils.invoice_utils import (
    InvoiceTotals,
    calculate_due_date,
    calculate_invoice_totals,
    generate_invoice_number,
    track_invoice_view
)

logger = logging.getLogger(__name__)


def get_status_value(status: InvoiceStatus) -> str:
    """Extract string value from status enum for logging/serialization."""
    return status.value


def _validate_client_exists(client_id: int, db: Session) -> Client:
    """Validate client exists and return it."""
    client = db.query(Client).filter(Client.id == client_id).first()

    if not client:
        raise NotFoundException(
            message=f"Client with id {client_id} not found",
            resource="client"
        )

    return client


def _validate_invoice_exists(invoice_id: int, db: Session) -> Invoice:
    """Validate invoice exists and return it."""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()

    if not invoice:
        raise NotFoundException(
            message=f"Invoice with id {invoice_id} not found",
            resource="invoice"
        )

    return invoice


ALLOWED_STATUS_TRANSITIONS: dict[InvoiceStatus, set[InvoiceStatus]] = {
    InvoiceStatus.DRAFT: {
        InvoiceStatus.SENT,
        InvoiceStatus.CANCELLED
    },
    InvoiceStatus.SENT: {
        InvoiceStatus.VIEWED,
        InvoiceStatus.PAID,
        InvoiceStatus.PARTIALLY_PAID,
        InvoiceStatus.OVERDUE,
        InvoiceStatus.CANCELLED
    },
    InvoiceStatus.VIEWED: {
        InvoiceStatus.PAID,
        InvoiceStatus.PARTIALLY_PAID,
        InvoiceStatus.OVERDUE,
        InvoiceStatus.CANCELLED
    },
    InvoiceStatus.PAID: set(),
    InvoiceStatus.PARTIALLY_PAID: {
        InvoiceStatus.PAID,
        InvoiceStatus.OVERDUE,
        InvoiceStatus.CANCELLED
    },
    InvoiceStatus.OVERDUE: {
        InvoiceStatus.PAID,
        InvoiceStatus.PARTIALLY_PAID,
        InvoiceStatus.CANCELLED
    },
    InvoiceStatus.CANCELLED: set()
}


def validate_status_transition(
    current_status: InvoiceStatus,
    new_status: InvoiceStatus
) -> None:
    """Validate that transitioning from current_status to new_status is allowed."""
    if current_status == new_status:
        return

    allowed_transitions = ALLOWED_STATUS_TRANSITIONS.get(current_status, set())

    if new_status not in allowed_transitions:
        allowed_list = (
            [s.value for s in allowed_transitions]
            if allowed_transitions
            else ["none (terminal state)"]
        )
        raise ValidationException(
            message=f"Invalid status transition from '{current_status.value}' to '{new_status.value}'",
            details=[{
                "field": "status",
                "current": current_status.value,
                "requested": new_status.value,
                "allowed": ', '.join(allowed_list)
            }]
        )


def create_invoice(
    invoice_data: InvoiceCreate,
    db: Session,
    payment_terms_days: int = 30,
    auto_generate_pdf: bool = False,
    auto_send_email: bool = False
) -> Invoice:
    """Create a new invoice with automation triggers."""
    with transaction_scope(db):
        client = _validate_client_exists(invoice_data.client_id, db)

        invoice_dict = invoice_data.model_dump(exclude={"items"})
        invoice = Invoice(**invoice_dict)

        if not invoice.invoice_due:
            current_date = get_current_timezone("Africa/Lagos")
            invoice.invoice_due = calculate_due_date(
                current_date, payment_terms_days
            )

        db.add(invoice)
        db.flush()

        invoice.invoice_no = generate_invoice_number(invoice.id)
        invoice.purchase_no = invoice.id

        for item_data in invoice_data.items:
            qty = Decimal(str(item_data.qty))
            rate = Decimal(str(item_data.rate))
            amount = (qty * rate).quantize(Decimal('0.01'))

            item = Item(
                item_desc=item_data.item_desc,
                qty=qty,
                rate=rate,
                amount=amount,
                invoice_id=invoice.id
            )
            db.add(item)

        db.flush()

        logger.info(
            f"Invoice {invoice.id} created with {len(invoice_data.items)} items",
            extra={
                "invoice_id": invoice.id,
                "invoice_no": invoice.invoice_no,
                "client_id": invoice.client_id,
                "client_name": client.name,
                "item_count": len(invoice_data.items),
                "due_date": invoice.invoice_due.isoformat()
            }
        )

        if auto_generate_pdf and auto_send_email:
            from app.core.celery_app import celery_app

            celery_app.send_task(
                'invoice.generate_and_send',
                args=[invoice.id]
            )
            logger.info(
                f"Triggered PDF generation + email task for invoice {invoice.id}",
                extra={"invoice_id": invoice.id, "task": "generate_and_send"}
            )
        elif auto_send_email:
            # Email only
            from app.core.celery_app import celery_app

            celery_app.send_task(
                'email.send_invoice',
                args=[invoice.id]
            )
            logger.info(
                f"Triggered email task for invoice {invoice.id}",
                extra={"invoice_id": invoice.id, "task": "send_email"}
            )

        return invoice


def update_invoice(
    invoice_id: int,
    invoice_data: InvoiceUpdate,
    db: Session
) -> Invoice:
    """Update an existing invoice (partial update)."""
    with transaction_scope(db):
        invoice = _validate_invoice_exists(invoice_id, db)

        update_data = invoice_data.model_dump(exclude_unset=True)

        if "status" in update_data and update_data["status"] is not None:
            new_status = update_data["status"]

            validate_status_transition(invoice.status, new_status)

        for field, value in update_data.items():
            setattr(invoice, field, value)

        db.flush()

        logger.info(
            f"Invoice {invoice_id} updated",
            extra={
                "invoice_id": invoice_id,
                "updated_fields": list(update_data.keys())
            }
        )

        return invoice


def change_invoice_status(
    invoice_id: int,
    new_status: InvoiceStatus,
    db: Session
) -> Invoice:
    """Change an invoice's status with validation."""
    with transaction_scope(db):
        invoice = _validate_invoice_exists(invoice_id, db)

        validate_status_transition(invoice.status, new_status)

        invoice.status = new_status
        db.flush()

        logger.info(
            f"Invoice {invoice_id} status changed",
            extra={
                "invoice_id": invoice_id,
                "old_status": invoice.status.value,
                "new_status": new_status.value
            }
        )

        return invoice


def delete_invoice(
    invoice_id: int,
    db: Session,
    allow_with_payments: bool = False
) -> None:
    """Delete an invoice and all related data (items, payments)."""
    with transaction_scope(db):
        invoice = db.query(Invoice)\
            .options(selectinload(Invoice.payments))\
            .filter(Invoice.id == invoice_id)\
            .first()

        if not invoice:
            raise NotFoundException(
                message=f"Invoice with id {invoice_id} not found",
                resource="invoice"
            )

        if not allow_with_payments and invoice.payments:
            raise ConflictException(
                message=f"Cannot delete invoice {invoice_id} because it has {len(invoice.payments)} payment(s)",
                code="INVOICE_HAS_PAYMENTS"
            )

        db.delete(invoice)

        logger.info(
            f"Invoice {invoice_id} deleted",
            extra={
                "invoice_id": invoice_id,
                "had_payments": len(invoice.payments) > 0
            }
        )


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
        raise NotFoundException(
            message=f"Invoice with id {invoice_id} not found",
            resource="invoice"
        )

    if track_view:
        with transaction_scope(db):
            track_invoice_view(invoice)

    totals = calculate_invoice_totals(invoice)

    return invoice, totals


def get_invoices_paginated(
    db: Session,
    page: int = 1,
    limit: int = 10,
    search: Optional[str] = None
) -> dict:
    """Get paginated list of invoices with optional search."""
    if limit < 1 or limit > 100:
        raise ValidationException(
            message="Pagination limit must be between 1 and 100",
            details=[{"field": "limit", "range": "1-100"}]
        )

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
