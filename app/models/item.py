from sqlalchemy import DECIMAL, BigInteger, Column, ForeignKey, Integer, String
from app.config.database import Base


from sqlalchemy.orm import relationship


class Item(Base):
    __tablename__ = "item"

    id = Column(BigInteger(), primary_key=True, index=True)
    item_desc = Column(String(150), nullable=False)
    qty = Column(Integer(), nullable=False)
    rate = Column(Integer, nullable=False)
    amount = Column(DECIMAL(15, 2), nullable=False)
    invoice_id = Column(BigInteger, ForeignKey(
        'invoice.id', ondelete='CASCADE'), nullable=False)

    invoice = relationship("Invoice", back_populates="items")

    def __repr__(self) -> str:
        return f"<Item(id={self.id}, desc='{self.item_desc[:30]}', amount={self.amount})>"
