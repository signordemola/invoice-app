from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..config.database import Base

if TYPE_CHECKING:
    from .client import Client
    from .payment import Payment
    from .item import Item
    from .recurrent_bill import RecurrentBill


class Invoice(Base):
    __tablename__ = "invoice"

    # Primary key
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)

    # Required fields
    invoice_no: Mapped[str | None] = mapped_column(
        String(30), unique=True, index=True, nullable=True
    )
    date_value: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now())
    invoice_due: Mapped[datetime] = mapped_column(DateTime)
    client_type: Mapped[int] = mapped_column(Integer)
    currency: Mapped[int] = mapped_column(Integer)
    client_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey('client.id', ondelete='RESTRICT'))

    # Optional fields
    purchase_no: Mapped[int | None] = mapped_column(Integer)

    # Discount fields
    disc_type: Mapped[str | None] = mapped_column(String(10))
    disc_value: Mapped[str | None] = mapped_column(String(10))
    disc_desc: Mapped[str | None] = mapped_column(Text)

    # Optional fields with defaults
    is_dummy: Mapped[int | None] = mapped_column(Integer, default=0)
    recurrent_bill_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey('recurrent_bill.id', ondelete='SET NULL')
    )

    # Tracking fields
    view_count: Mapped[int | None] = mapped_column(Integer, default=0)
    last_view: Mapped[datetime | None] = mapped_column(DateTime)

    # Reminder fields
    send_reminders: Mapped[bool | None] = mapped_column(Boolean, default=False)
    reminder_frequency: Mapped[int | None] = mapped_column(Integer)
    reminder_logs: Mapped[dict | None] = mapped_column(JSON)

    # Relationships
    client: Mapped["Client"] = relationship(back_populates="invoices")
    items: Mapped[list["Item"]] = relationship(
        back_populates="invoice", cascade="all, delete-orphan")
    payments: Mapped[list["Payment"]] = relationship(
        back_populates="invoice", cascade="all, delete-orphan")
    recurrent_bill: Mapped["RecurrentBill | None"] = relationship(
        back_populates="invoices")

    def __repr__(self) -> str:
        return f"<Invoice(id={self.id}, invoice_no='{self.invoice_no}', client_id={self.client_id})>"
