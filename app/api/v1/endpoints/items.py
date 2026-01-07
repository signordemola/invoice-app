from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.config.database import get_db
from app.models.user import User
from app.schemas.item import ItemCreate, ItemResponse, ItemUpdate
from app.services.item_service import add_item_to_invoice, delete_item, get_invoice_items, update_item


router = APIRouter()


@router.post('/{invoice_id}', response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def add_item_to_invoice_route(
    invoice_id: int,
    item_data: ItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a new item to an existing invoice"""
    return add_item_to_invoice(invoice_id, item_data, db)


@router.patch('/{item_id}', response_model=ItemResponse)
def update_item_route(
    item_id: int,
    item_data: ItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing item (partial update)"""
    return update_item(item_id, item_data, db)


@router.delete('/{item_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_item_route(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an item from an invoice"""
    delete_item(item_id, db, allow_last_item_delete=False)
    return None


@router.get('/{invoice_id}', response_model=list[ItemResponse])
def get_invoice_items_route(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all items for a specific invoice"""
    return get_invoice_items(invoice_id, db)
