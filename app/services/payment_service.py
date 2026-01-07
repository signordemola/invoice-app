from decimal import Decimal
import logging
from math import ceil
from typing import Optional

from sqlalchemy.orm import joinedload, Session

from app.core.exceptions import ConflictException, NotFoundException
from app.models.invoice import Invoice, InvoiceStatus
from app.models.payment import InvoicePaymentState, Payment, PaymentStatus
from app.schemas.payment import PaymentCreate, PaymentUpdate
from app.services.database import transaction_scope
from app.utils.invoice_utils import calculate_invoice_totals

logger = logging.getLogger(__name__)


"""
TODO: After successful creation, enqueue background job to:
      - Send payment confirmation email
      - Update accounting system
      - Trigger webhook notifications
"""


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_status_value(status: InvoiceStatus | PaymentStatus | InvoicePaymentState) -> str:
    """Extract string value from status enum for logging/serialization."""

    return status.value


def calculate_remaining_balance(invoice: Invoice) -> Decimal:
    """Calculate the remaining balance owed on an invoice."""

    totals = calculate_invoice_totals(invoice)
    invoice_total = totals["vat_total"]

    total_paid = sum(
        payment.amount_paid
        for payment in invoice.payments
        if payment.status != PaymentStatus.CANCELLED
    )

    remaining = invoice_total - Decimal(str(total_paid))
    return remaining


def determine_payment_status(invoice: Invoice) -> InvoicePaymentState:
    """Determine invoice payment state based on payments received."""

    remaining_balance = calculate_remaining_balance(invoice)
    totals = calculate_invoice_totals(invoice)
    invoice_total = totals["vat_total"]

    if remaining_balance == 0:
        return InvoicePaymentState.FULLY_PAID
    elif remaining_balance < 0:
        return InvoicePaymentState.OVERPAID
    elif remaining_balance < invoice_total:
        return InvoicePaymentState.PARTIALLY_PAID
    else:
        return InvoicePaymentState.UNPAID


# ============================================================================
# PRIVATE VALIDATION HELPERS
# ============================================================================

def _validate_invoice_exists(invoice_id: int, db: Session) -> Invoice:
    """Validate invoice exists and return it."""

    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()

    if not invoice:
        raise NotFoundException(
            message=f"Invoice with id {invoice_id} not found",
            resource="invoice"
        )

    return invoice


def _validate_payment_reference_unique(
    invoice_id: int,
    reference_number: Optional[str],
    db: Session
) -> None:
    """Validate payment reference number is unique for this invoice."""

    if not reference_number:
        return

    existing_payment = db.query(Payment).filter(
        Payment.invoice_id == invoice_id,
        Payment.reference_number == reference_number
    ).first()

    if existing_payment:
        raise ConflictException(
            message=f"Payment with reference '{reference_number}' "
            f"already exists for invoice {invoice_id}",
            code="DUPLICATE_PAYMENT_REFERENCE"
        )


def _create_payment_record(payment_data: PaymentCreate, db: Session) -> Payment:
    """Create and persist payment record (no commit)."""

    payment_dict = payment_data.model_dump()
    payment = Payment(**payment_dict)

    db.add(payment)
    db.flush()

    return payment


def _update_invoice_status_after_payment(invoice: Invoice, db: Session) -> None:
    """Update invoice status based on payment activity."""

    payment_status = determine_payment_status(invoice)

    if payment_status == InvoicePaymentState.FULLY_PAID:
        invoice.status = InvoiceStatus.PAID
    elif payment_status == InvoicePaymentState.OVERPAID:
        invoice.status = InvoiceStatus.PAID
    elif payment_status == InvoicePaymentState.PARTIALLY_PAID:
        invoice.status = InvoiceStatus.PARTIALLY_PAID


# ============================================================================
# PUBLIC SERVICE FUNCTIONS - READ OPERATIONS
# ============================================================================

def get_payment_by_id(
    payment_id: int,
    db: Session,
    load_invoice: bool = True
) -> Payment:
    """Retrieve a single payment by ID."""

    query = db.query(Payment)

    if load_invoice:
        query = query.options(joinedload(Payment.invoice))

    payment = query.filter(Payment.id == payment_id).first()

    if not payment:
        raise NotFoundException(
            message=f"Payment with id {payment_id} not found",
            resource="payment"
        )

    return payment


def get_payments_for_invoice(invoice_id: int, db: Session) -> list[Payment]:
    """Retrieve all payments for a specific invoice."""

    payments = db.query(Payment)\
        .filter(Payment.invoice_id == invoice_id)\
        .order_by(Payment.payment_date.asc())\
        .all()

    return payments


def get_payments_paginated(
    db: Session,
    page: int = 1,
    limit: int = 10
) -> dict:
    """Retrieve all payments with pagination."""

    if limit < 1 or limit > 100:
        raise ValueError("Limit can only be between 1 and 100")

    query = db.query(Payment).order_by(Payment.date_created.desc())
    total = query.count()

    skip = (page - 1) * limit
    payments = query.offset(skip).limit(limit).all()

    total_pages = ceil(total / limit) if total > 0 else 0

    return {
        "payments": payments,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages
        }
    }


# ============================================================================
# PUBLIC SERVICE FUNCTIONS - WRITE OPERATIONS
# ============================================================================

def create_payment(payment_data: PaymentCreate, db: Session) -> Payment:
    """Create a new payment record for an invoice."""

    with transaction_scope(db):
        _validate_invoice_exists(payment_data.invoice_id, db)
        _validate_payment_reference_unique(
            payment_data.invoice_id,
            payment_data.reference_number,
            db
        )

        payment = _create_payment_record(payment_data, db)
        return payment


def create_payment_and_update_invoice(
    payment_data: PaymentCreate,
    db: Session
) -> Payment:
    """Atomically create a payment and update the invoice status."""

    with transaction_scope(db):
        invoice = _validate_invoice_exists(payment_data.invoice_id, db)
        _validate_payment_reference_unique(
            payment_data.invoice_id,
            payment_data.reference_number,
            db
        )

        payment = _create_payment_record(payment_data, db)
        _update_invoice_status_after_payment(invoice, db)

        logger.info(
            f"Payment {payment.id} created and invoice {invoice.id} "
            f"status updated to {invoice.status}",
            extra={
                "payment_id": payment.id,
                "invoice_id": invoice.id,
                "amount": float(payment.amount_paid),
                "new_status": get_status_value(invoice.status)
            }
        )

        return payment


def update_payment(
    payment_id: int,
    payment_data: PaymentUpdate,
    db: Session
) -> Payment:
    """Update an existing payment (partial update)."""

    with transaction_scope(db):
        payment = db.query(Payment).filter(Payment.id == payment_id).first()

        if not payment:
            raise NotFoundException(
                message=f"Payment with id {payment_id} not found",
                resource="payment"
            )

        update_data = payment_data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(payment, field, value)

        db.flush()
        return payment


def delete_payment(payment_id: int, db: Session) -> None:
    """Delete a payment record."""

    with transaction_scope(db):
        payment = db.query(Payment).filter(Payment.id == payment_id).first()

        if not payment:
            raise NotFoundException(
                message=f"Payment with id {payment_id} not found",
                resource="payment"
            )

        db.delete(payment)


def delete_payment_and_update_invoice(payment_id: int, db: Session) -> int:
    """Atomically delete a payment and update the invoice status."""

    with transaction_scope(db):
        payment = db.query(Payment).filter(Payment.id == payment_id).first()

        if not payment:
            raise NotFoundException(
                message=f"Payment with id {payment_id} not found",
                resource="payment"
            )

        invoice = payment.invoice
        invoice_id = payment.invoice_id

        db.delete(payment)
        db.flush()

        _update_invoice_status_after_payment(invoice, db)

        logger.info(
            f"Payment {payment_id} deleted and invoice {invoice_id} "
            f"status updated to {invoice.status}",
            extra={
                "payment_id": payment_id,
                "invoice_id": invoice_id,
                "new_status": get_status_value(invoice.status)
            }
        )

        return invoice_id
