from sqlalchemy import Column, String, Text, BigInteger, Integer, DateTime, Boolean, JSON, ForeignKey, func
from sqlalchemy.orm import relationship
from ..config.database import Base


class Invoice(Base):
    __tablename__ = "invoice"

    id = Column(BigInteger, primary_key=True, index=True)
    invoice_no = Column(String(30), nullable=False, unique=True, index=True)
    purchase_no = Column(Integer, nullable=True)
    date_value = Column(DateTime, nullable=False, server_default=func.now())
    invoice_due = Column(DateTime, nullable=False)

    # Discount fields
    disc_type = Column(String(10), nullable=True)
    disc_value = Column(String(10), nullable=True)
    disc_desc = Column(Text, nullable=True)

    # Client and type
    client_type = Column(Integer, nullable=False)
    currency = Column(Integer, nullable=False)
    client_id = Column(BigInteger, ForeignKey(
        'client.id', ondelete='RESTRICT'), nullable=False)

    # Optional fields
    is_dummy = Column(Integer, nullable=True, default=0)
    recurrent_bill_id = Column(BigInteger, ForeignKey(
        'recurrent_bill.id', ondelete='SET NULL'), nullable=True)

    # Tracking fields
    view_count = Column(Integer, nullable=True, default=0)
    last_view = Column(DateTime, nullable=True)

    # Reminder fields
    send_reminders = Column(Boolean, nullable=True, default=False)
    reminder_frequency = Column(Integer, nullable=True)
    reminder_logs = Column(JSON, nullable=True)

    # Relationships
    client = relationship("Client", back_populates="invoices")
    items = relationship("Item", back_populates="invoice",
                         cascade="all, delete-orphan")
    payments = relationship(
        "Payment", back_populates="invoice", cascade="all, delete-orphan")
    recurrent_bill = relationship("RecurrentBill", back_populates="invoices")

    def __repr__(self) -> str:
        return f"<Invoice(id={self.id}, invoice_no='{self.invoice_no}', client_id={self.client_id})>"
