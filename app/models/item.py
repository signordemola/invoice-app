from decimal import Decimal
from sqlalchemy import DECIMAL, BigInteger, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..config.database import Base
from .invoice import Invoice


class Item(Base):
    __tablename__ = "item"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    item_desc: Mapped[str] = mapped_column(String(150))
    qty: Mapped[int] = mapped_column(Integer)
    rate: Mapped[int] = mapped_column(Integer)
    amount: Mapped[Decimal] = mapped_column(DECIMAL(15, 2))
    invoice_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey('invoice.id', ondelete='CASCADE'))

    invoice: Mapped["Invoice"] = relationship(back_populates="items")

    def __repr__(self) -> str:
        return f"<Item(id={self.id}, desc='{self.item_desc[:30]}', amount={self.amount})>"
