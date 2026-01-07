from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.config.database import get_db
from app.models.invoice import Invoice
from app.schemas.payment import PaymentCreate, PaymentPaginatedResponse, PaymentResponse, PaymentUpdate
from app.services.email_service import EmailServiceError, send_payment_reminder
from app.services.payment_service import create_payment_and_update_invoice, delete_payment_and_update_invoice, get_payment_by_id, get_payments_for_invoice, get_payments_paginated, update_payment

router = APIRouter()


@router.post('/', response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment_route(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Create a new payment record and update invoice status."""

    return create_payment_and_update_invoice(payment_data=payment_data, db=db)


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment_route(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Retrieve a single payment by ID."""

    return get_payment_by_id(payment_id=payment_id, db=db)


@router.get("/", response_model=PaymentPaginatedResponse)
def get_payments_route(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get paginated list of all payments."""

    return get_payments_paginated(db=db, page=page, limit=limit)


@router.get("/invoice/{invoice_id}", response_model=list[PaymentResponse])
def get_invoice_payments_route(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get all payments for a specific invoice."""

    return get_payments_for_invoice(invoice_id=invoice_id, db=db)


@router.patch("/{payment_id}", response_model=PaymentResponse)
def update_payment_route(
    payment_id: int,
    payment_data: PaymentUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Update an existing payment (partial update)."""

    return update_payment(
        payment_id=payment_id,
        payment_data=payment_data,
        db=db
    )


@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment_route(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Delete a payment record."""

    delete_payment_and_update_invoice(
        payment_id=payment_id, db=db)
    return None


# TODO: add to background task

@router.post("/{invoice_id}/remind", status_code=status.HTTP_200_OK)
def send_payment_reminder_route(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Manually send payment reminder for overdue invoice."""

    email_id = send_payment_reminder(invoice_id, db)

    return {
        "message": "Payment reminder sent successfully",
        "email_id": email_id,
        "invoice_id": invoice_id
    }
