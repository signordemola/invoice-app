from fastapi import APIRouter, HTTPException, Query, Response, status, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.config.database import get_db
from app.models.invoice import Invoice
from app.schemas.invoice import InvoiceCreate, InvoicePaginatedResponse, InvoiceResponse, InvoiceStatusUpdate, InvoiceUpdate
from app.services.invoice_service import change_invoice_status, create_invoice, delete_invoice, get_invoice_by_id, get_invoices_paginated, update_invoice
from app.services.pdf_service import PDFInvoiceNotFoundError, generate_invoice_pdf


router = APIRouter()


@router.post('/', response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_invoice_route(invoice_data: InvoiceCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Create a new invoice"""

    invoice = create_invoice(
        invoice_data=invoice_data,
        db=db,
        payment_terms_days=30,
        auto_generate_pdf=True,
        auto_send_email=True
    )

    return invoice


@router.get('/', response_model=InvoicePaginatedResponse)
def get_paginated_invoices_route(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: str | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get paginated list of invoices with optional search (client name/email)"""

    return get_invoices_paginated(db, page=page, limit=limit, search=search)


@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice_route(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get a single invoice by ID."""

    invoice, _ = get_invoice_by_id(invoice_id, db, load_relationships=True)
    return invoice


@router.patch('/{invoice_id}/status', response_model=InvoiceResponse)
def change_invoice_status_route(invoice_id: int, status_update: InvoiceStatusUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Change an invoice's status with validation of allowed transitions."""

    invoice = change_invoice_status(
        invoice_id=invoice_id,
        new_status=status_update.status,
        db=db
    )

    return invoice


@router.patch("/{invoice_id}", response_model=InvoiceResponse)
def update_invoice_route(
    invoice_id: int,
    invoice_update: InvoiceUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Partially update an invoice (only mutable fields)."""

    return update_invoice(invoice_id, invoice_update, db)


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_invoice_route(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Delete an invoice (fails if it has payments unless forced)."""

    delete_invoice(invoice_id, db, allow_with_payments=False)
    return None


# move to background tasks
@router.get("/{invoice_id}/pdf")
def download_invoice_pdf_route(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Generate and download invoice as PDF."""

    try:
        pdf_bytes = generate_invoice_pdf(invoice_id=invoice_id, db=db)

        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        filename = f"{invoice.invoice_no}.pdf" if invoice and invoice.invoice_no else f"invoice_{invoice_id}.pdf"

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except PDFInvoiceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{invoice_id}/send", status_code=status.HTTP_200_OK)
def send_invoice_email_route(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Manually send invoice email to client."""

    invoice, _ = get_invoice_by_id(invoice_id, db, track_view=False)

    from app.core.celery_app import celery_app
    
    task = celery_app.send_task(
        'email.send_invoice',
        args=[invoice_id]
    )

    return {
        "message": "Invoice email queued for sending",
        "invoice_id": invoice_id,
        "invoice_no": invoice.invoice_no,
        "client_email": invoice.client.email,
        "task_id": task.id
    }
