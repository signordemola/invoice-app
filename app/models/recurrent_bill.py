from sqlalchemy import Column, Integer, String, BigInteger, DECIMAL, DateTime, ForeignKey, Index, func
from sqlalchemy.orm import relationship
from ..config.database import Base


class RecurrentBill(Base):
    __tablename__ = "recurrent_bill"

    __table_args__ = (
        Index('recurrent_bill_args_req', 'id', 'client_id'),
    )

    id = Column(BigInteger, primary_key=True, index=True)
    client_id = Column(BigInteger, ForeignKey(
        'client.id', ondelete='CASCADE'), nullable=False)
    product_name = Column(String(150), nullable=False)
    amount_expected = Column(DECIMAL(15, 2), nullable=False)
    date_created = Column(DateTime, nullable=False, server_default=func.now())
    date_due = Column(DateTime, nullable=False)
    date_updated = Column(DateTime, nullable=False,
                          server_default=func.now(), onupdate=func.now())
    payment_status = Column(Integer, nullable=False, default=0)

    client = relationship("Client")
    invoices = relationship(
        "Invoice", back_populates="recurrent_bill")

    def __repr__(self) -> str:
        return f"<RecurrentBill(id={self.id}, product='{self.product_name}', status={self.payment_status})>"
