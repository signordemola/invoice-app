from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from sqlalchemy import BigInteger, DECIMAL, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..config.database import Base
from .invoice import Invoice


class Payment(Base):
    __tablename__ = "payment"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    client_name: Mapped[str] = mapped_column(String(150))
    payment_desc: Mapped[str | None] = mapped_column(Text)
    date_created: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now())
    payment_mode: Mapped[int] = mapped_column(Integer)
    amount_paid: Mapped[Decimal] = mapped_column(DECIMAL(15, 2))
    balance: Mapped[Decimal | None] = mapped_column(DECIMAL(15, 2))
    invoice_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey('invoice.id', ondelete='CASCADE'))
    status: Mapped[int] = mapped_column(Integer, default=0)
    view_count: Mapped[int | None] = mapped_column(Integer, default=0)
    last_view: Mapped[datetime | None] = mapped_column(DateTime)

    invoice: Mapped["Invoice"] = relationship(back_populates="payments")

    def __repr__(self) -> str:
        return f"<Payment(id={self.id}, invoice_id={self.invoice_id}, amount={self.amount_paid})>"
