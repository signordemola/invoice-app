from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from sqlalchemy import BigInteger, DECIMAL, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..config.database import Base
from .invoice import Invoice
from enum import Enum as PyEnum


class PaymentMode(str, PyEnum):
    """Valid payment method values"""
    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    CHECK = "check"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    MOBILE_PAYMENT = "mobile_payment"
    OTHER = "other"


class PaymentStatus(str, PyEnum):
    """Valid payment status values"""
    PENDING = "pending"
    PARTIAL = 'partial'
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class InvoicePaymentState(str, PyEnum):
    """Aggregate payment state for an invoice."""
    FULLY_PAID = "fully_paid"
    OVERPAID = "overpaid"
    PARTIALLY_PAID = "partially_paid"
    UNPAID = "unpaid"


class Payment(Base):
    __tablename__ = "payment"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    client_name: Mapped[str] = mapped_column(String(150))
    payment_desc: Mapped[str | None] = mapped_column(Text)

    payment_date: Mapped[datetime] = mapped_column(DateTime)
    date_created: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now())
    payment_mode: Mapped[str] = mapped_column(
        Enum(PaymentMode, native_enum=False, length=20),
        nullable=False
    )
    reference_number: Mapped[str | None] = mapped_column(
        String(100), nullable=True)
    amount_paid: Mapped[Decimal] = mapped_column(DECIMAL(15, 2))
    invoice_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey('invoice.id', ondelete='CASCADE'))
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, native_enum=False, length=20),
        default=PaymentStatus.COMPLETED,
        nullable=False
    )
    view_count: Mapped[int | None] = mapped_column(Integer, default=0)
    last_view: Mapped[datetime | None] = mapped_column(DateTime)

    invoice: Mapped["Invoice"] = relationship(back_populates="payments")

    def __repr__(self) -> str:
        return f"<Payment(id={self.id}, invoice_id={self.invoice_id}, amount={self.amount_paid})>"
