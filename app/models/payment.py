from sqlalchemy import Column, String, Text, BigInteger, Integer, DECIMAL, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from ..config.database import Base


class Payment(Base):
    __tablename__ = "payment"

    id = Column(BigInteger, primary_key=True, index=True)
    client_name = Column(String(150), nullable=False)
    payment_desc = Column(Text, nullable=True)
    date_created = Column(DateTime, nullable=False, server_default=func.now())
    payment_mode = Column(Integer, nullable=False)
    amount_paid = Column(DECIMAL(15, 2), nullable=False)
    balance = Column(DECIMAL(15, 2), nullable=True)
    invoice_id = Column(BigInteger, ForeignKey(
        'invoice.id', ondelete='CASCADE'), nullable=False)
    status = Column(Integer, nullable=False, default=0)
    view_count = Column(Integer, nullable=True, default=0)
    last_view = Column(DateTime, nullable=True)

    invoice = relationship("Invoice", back_populates="payments")

    def __repr__(self) -> str:
        return f"<Payment(id={self.id}, invoice_id={self.invoice_id}, amount={self.amount_paid})>"
