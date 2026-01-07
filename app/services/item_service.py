from decimal import ROUND_HALF_UP, Decimal
import logging
from sqlalchemy.orm import Session
from app.core.exceptions import ConflictException, NotFoundException
from app.models.invoice import Invoice
from app.models.item import Item
from app.schemas.item import ItemCreate, ItemUpdate
from app.services.database import transaction_scope

logger = logging.getLogger(__name__)


def add_item_to_invoice(
    invoice_id: int,
    item_data: ItemCreate,
    db: Session
) -> Item:
    """Add a new line item to an existing invoice with transactional integrity."""

    with transaction_scope(db):
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise NotFoundException(
                message=f"Invoice with id {invoice_id} not found",
                resource="invoice"
            )

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
        db.flush()

        return item


def update_item(
    item_id: int,
    item_data: ItemUpdate,
    db: Session
) -> Item:
    """Update an existing item with transactional integrity."""

    with transaction_scope(db):
        item = db.query(Item).filter(Item.id == item_id).first()
        if not item:
            raise NotFoundException(
                message=f"Item with id {item_id} not found",
                resource="item"
            )

        update_data = item_data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(item, field, value)

        if 'qty' in update_data or 'rate' in update_data:
            qty = Decimal(str(item.qty))
            rate = Decimal(str(item.rate))
            item.amount = (qty * rate).quantize(
                Decimal('0.01'),
                rounding=ROUND_HALF_UP
            )

        db.flush()

        return item


def delete_item(
    item_id: int,
    db: Session,
    allow_last_item_delete: bool = False
) -> None:
    """Delete an item from an invoice with business rule validation."""

    with transaction_scope(db):
        item = db.query(Item).filter(Item.id == item_id).first()
        if not item:
            raise NotFoundException(
                message=f"Item with id {item_id} not found",
                resource="item"
            )

        if not allow_last_item_delete:
            item_count = db.query(Item)\
                .filter(Item.invoice_id == item.invoice_id)\
                .count()

            if item_count == 1:
                raise ConflictException(
                    message=f"Cannot delete the last item from invoice {item.invoice_id}. "
                    "Invoices must have at least one line item.",
                    code="LAST_ITEM_DELETION_FORBIDDEN"
                )

        db.delete(item)


def get_invoice_items(invoice_id: int, db: Session) -> list[Item]:
    """Get all items for a specific invoice."""

    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise NotFoundException(
            message=f"Invoice with id {invoice_id} not found",
            resource="invoice"
        )

    items = db.query(Item)\
        .filter(Item.invoice_id == invoice_id)\
        .order_by(Item.id.asc())\
        .all()

    return items
