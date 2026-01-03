from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.config.database import get_db
from app.models.invoice import Invoice
from app.schemas.payment import PaymentCreate, PaymentPaginatedResponse, PaymentResponse, PaymentUpdate
from app.services.invoice_service import InvoiceNotFoundError
from app.services.payment_service import DuplicatePaymentError, InvalidPaymentDataError, PaymentNotFoundError, PaymentServiceError, create_payment, get_payment_by_id, get_payments_paginated, update_invoice_status_after_payment

router = APIRouter()


@router.post('/', response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment_route(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Create a new payment record and update invoice status."""

    try:
        new_payment = create_payment(payment_data=payment_data, db=db)

        invoice = db.query(Invoice).filter(
            Invoice.id == new_payment.invoice_id).first()

        if invoice:
            update_invoice_status_after_payment(invoice, db)

        return new_payment
    except InvoiceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except DuplicatePaymentError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except (InvalidPaymentDataError, PaymentServiceError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment_route(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Retrieve a single payment by ID."""

    try:
        payment = get_payment_by_id(
            payment_id=payment_id,
            db=db,
            load_invoice=True
        )
        return payment
    except PaymentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/", response_model=PaymentPaginatedResponse)
def get_payments_route(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get paginated list of all payments."""

    try:
        return get_payments_paginated(db=db, page=page, limit=limit)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
