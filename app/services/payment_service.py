from decimal import Decimal
from math import ceil
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import Session

from app.models.invoice import Invoice, InvoiceStatus
from app.models.payment import Payment
from app.schemas.payment import PaymentCreate, PaymentUpdate
from app.utils.invoice_utils import calculate_invoice_totals


class PaymentServiceError(Exception):
    """Base exception for payment service errors"""
    pass


class PaymentNotFoundError(PaymentServiceError):
    """Raised when a payment is not found"""
    pass


class InvalidPaymentDataError(PaymentServiceError):
    """Raised when payment data is invalid (e.g., negative amount, future dates)"""
    pass


class InvoiceNotFoundError(PaymentServiceError):
    """Raised when the specified invoice doesn't exist"""
    pass


class DuplicatePaymentError(PaymentServiceError):
    """Raised when attempting to create a duplicate payment (same reference number)"""
    pass


def create_payment(
        payment_data: PaymentCreate,
        db: Session

) -> Payment:
    """Create a new payment record for an invoice."""

    invoice = db.query(Invoice).filter(
        Invoice.id == payment_data.invoice_id).first()
    if not invoice:
        raise InvoiceNotFoundError(
            f"Invoice with id {payment_data.invoice_id} not found")

    if payment_data.reference_number:
        existing_payment = db.query(Payment).filter(
            Payment.invoice_id == payment_data.invoice_id,
            Payment.reference_number == payment_data.reference_number
        ).first()

        if existing_payment:
            raise DuplicatePaymentError(
                f"Payment with reference '{payment_data.reference_number}' "
                f"already exists for invoice {payment_data.invoice_id}"
            )

    payment_dict = payment_data.model_dump()
    payment = Payment(**payment_dict)

    db.add(payment)
    db.commit()
    db.refresh(payment)

    return payment


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
        raise PaymentNotFoundError(f"Payment with id {payment_id} not found")

    return payment


def get_payments_for_invoice(
    invoice_id: int,
    db: Session
) -> list[Payment]:
    """Retrieve all payments for a specific invoice."""

    payments = db.query(Payment)\
        .filter(Payment.invoice_id == invoice_id)\
        .order_by(Payment.payment_date.asc())\
        .all()

    return payments


def get_payments_paginated(db: Session, page: int = 1, limit: int = 10) -> dict:
    """Retrieve all payments with pagination."""

    if limit < 1 or limit > 100:
        raise ValueError("Limit can only be between 1 and 100")

    query = db.query(Payment).order_by(Payment.date_created.desc())

    total = query.count()

    skip = (page-1) * limit
    payments = query.offset(skip).limit(limit).all()

    total_pages = ceil(total/limit) if total > 0 else 0

    return {
        "payments": payments,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages
        }
    }


def update_payment(payment_id: int, payment_data: PaymentUpdate, db: Session) -> Payment:
    """Update an existing payment (partial update)."""

    payment = db.query(Payment).filter(Payment.id == payment_id).first()

    if not payment:
        raise PaymentNotFoundError(f"Payment with id {payment_id} not found")

    update_data = payment_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(payment, field, value)

    db.commit()
    db.refresh(payment)

    return payment


def update_invoice_status_after_payment(
    invoice: Invoice,
    db: Session
) -> None:
    """Update invoice status based on payment activity."""

    payment_status = determine_payment_status(invoice)

    if payment_status == "fully_paid":
        invoice.status = InvoiceStatus.PAID
    elif payment_status == "overpaid":
        invoice.status = InvoiceStatus.PAID
    elif payment_status == "partially_paid":
        invoice.status = InvoiceStatus.PARTIALLY_PAID

    db.commit()


def delete_payment(
    payment_id: int,
    db: Session
) -> None:
    """Delete a payment record."""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()

    if not payment:
        raise PaymentNotFoundError(f"Payment with id {payment_id} not found")

    db.delete(payment)
    db.commit()


def calculate_remaining_balance(invoice: Invoice) -> Decimal:
    """Calculate the remaining balance owed on an invoice."""

    totals = calculate_invoice_totals(invoice)
    invoice_total = totals["vat_total"]

    total_paid = sum(
        payment.amount_paid
        for payment in invoice.payments
        if payment.status != "cancelled"
    )

    remaining = invoice_total - Decimal(str(total_paid))

    return remaining


def determine_payment_status(invoice: Invoice) -> str:
    """Determine the payment status of an invoice based on payments received."""

    remaining_balance = calculate_remaining_balance(invoice)
    totals = calculate_invoice_totals(invoice)
    invoice_total = totals["vat_total"]

    if remaining_balance == 0:
        return "fully_paid"
    elif remaining_balance < 0:
        return "overpaid"
    elif remaining_balance < invoice_total:
        return "partially_paid"
    else:
        return "unpaid"
