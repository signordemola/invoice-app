from fastapi import APIRouter, HTTPException, Query, Request, status, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.config.database import get_db
from app.schemas.invoice import InvoiceCreate, InvoicePaginatedResponse, InvoiceResponse, InvoiceUpdate
from app.services.invoice_service import ClientNotFoundError, InvalidInvoiceDataError, InvoiceNotFoundError, InvoiceServiceError, create_invoice, delete_invoice, get_invoice_by_id, get_invoices_paginated, update_invoice


router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


@router.get("/dashboard", response_class=HTMLResponse)
def list_invoices(request: Request, db: Session = Depends(get_db)):
    result = get_invoices_paginated(
        db, page=1, limit=100)

    invoices = result["invoices"]

    return templates.TemplateResponse(
        "invoices.html",
        {"request": request, "invoices": invoices})


@router.post('/', response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_invoice_route(invoice_data: InvoiceCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Create a new invoice"""

    try:
        new_invoice = create_invoice(
            invoice_data=invoice_data,
            db=db,
            payment_terms_days=30,
            auto_generate_pdf=True,
            auto_send_email=True
        )
        return new_invoice
    except ClientNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except InvoiceServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get('/', response_model=InvoicePaginatedResponse)
def get_paginated_invoices_route(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: str | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get paginated list of invoices with optional search (client name/email)"""

    try:
        return get_invoices_paginated(db, page=page, limit=limit, search=search)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice_route(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get a single invoice by ID."""
    try:
        invoice, _ = get_invoice_by_id(invoice_id, db, load_relationships=True)
        return invoice
    except InvoiceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{invoice_id}", response_model=InvoiceResponse)
def update_invoice_route(
    invoice_id: int,
    invoice_update: InvoiceUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Partially update an invoice (only mutable fields)."""

    try:
        return update_invoice(invoice_id, invoice_update, db)
    except InvoiceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidInvoiceDataError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_invoice_route(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Delete an invoice (fails if it has payments unless forced)."""

    try:
        delete_invoice(invoice_id, db, allow_with_payments=False)
        return None
    except InvoiceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidInvoiceDataError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
