from decimal import ROUND_HALF_UP, Decimal
from sqlalchemy.orm import Session
from app.models.invoice import Invoice
from app.models.item import Item
from app.schemas.item import ItemCreate, ItemUpdate


class ItemServiceError(Exception):
    """Base exception for item service errors"""
    pass


class ItemNotFoundError(ItemServiceError):
    """Raised when an item is not found"""
    pass


class ItemInvoiceNotFoundError(ItemServiceError):
    """Raised when the invoice for an item doesn't exist"""
    pass


class InvalidItemDataError(ItemServiceError):
    """Raised when item data is invalid"""
    pass


class InvoiceHasNoItemsError(ItemServiceError):
    """Raised when trying to delete the last item from an invoice"""
    pass


def add_item_to_invoice(
    invoice_id: int,
    item_data: ItemCreate,
    db: Session
) -> Item:
    """Add a new line item to an existing invoice."""

    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise ItemInvoiceNotFoundError(
            f"Invoice with id {invoice_id} not found!")

    qty = Decimal(str(item_data.qty))
    rate = Decimal(str(item_data.rate))
    amount = (qty * rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    item = Item(
        item_desc=item_data.item_desc,
        qty=item_data.qty,
        rate=item_data.rate,
        amount=amount,
        invoice_id=invoice_id
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    return item


def update_item(
    item_id: int,
    item_data: ItemUpdate,
    db: Session
) -> Item:
    """Update an existing item (partial update)"""

    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise ItemNotFoundError(f"Item with id {item_id} not found!")

    update_data = item_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(item, field, value)

    if 'qty' in update_data or 'rate' in update_data:
        qty = Decimal(str(item.qty))
        rate = Decimal(str(item.rate))
        item.amount = (qty * rate).quantize(Decimal('0.01'),
                                            rounding=ROUND_HALF_UP)

    db.commit()
    db.refresh(item)

    return item


def delete_item(
    item_id: int,
    db: Session,
    allow_last_item_delete: bool = False
) -> None:
    """Delete an item from an invoice."""

    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise ItemNotFoundError(f"Item with id {item_id} not found!")

    if not allow_last_item_delete:
        item_count = db.query(Item)\
            .filter(Item.invoice_id == item.invoice_id)\
            .count()

        if item_count == 1:
            raise InvoiceHasNoItemsError(
                f"Cannot delete item {item_id} because it's the last item on invoice {item.invoice_id}. "
                "Invoices must have at least one line item."
            )

    # Delete the item
    db.delete(item)
    db.commit()


def get_invoice_items(invoice_id: int, db: Session) -> list[Item]:
    """Get all items for a specific invoice."""

    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise ItemInvoiceNotFoundError(
            f"Invoice with id {invoice_id} not found")

    items = db.query(Item)\
        .filter(Item.invoice_id == invoice_id)\
        .order_by(Item.id.asc())\
        .all()

    return items
