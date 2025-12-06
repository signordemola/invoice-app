from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from sqlalchemy import BigInteger, DECIMAL, DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..config.database import Base
from .client import Client
from .invoice import Invoice


class RecurrentBill(Base):
    __tablename__ = "recurrent_bill"

    __table_args__ = (
        Index('recurrent_bill_args_req', 'id', 'client_id'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    client_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey('client.id', ondelete='CASCADE'))
    product_name: Mapped[str] = mapped_column(String(150))
    amount_expected: Mapped[Decimal] = mapped_column(DECIMAL(15, 2))
    date_created: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now())
    date_due: Mapped[datetime] = mapped_column(DateTime)
    date_updated: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now())
    payment_status: Mapped[int] = mapped_column(Integer, default=0)

    client: Mapped["Client"] = relationship()
    invoices: Mapped[list["Invoice"]] = relationship(
        back_populates="recurrent_bill")

    def __repr__(self) -> str:
        return f"<RecurrentBill(id={self.id}, product='{self.product_name}', status={self.payment_status})>"
