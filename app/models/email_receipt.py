from sqlalchemy import Column, String, BigInteger, DateTime, func
from ..config.database import Base


class EmailReceipt(Base):
    __tablename__ = "email_receipt_count"

    id = Column(BigInteger, primary_key=True, index=True)
    ref = Column(String(240), nullable=False, index=True)
    counter = Column(BigInteger, nullable=False, default=0)
    last_received = Column(DateTime, nullable=False, server_default=func.now())
    body = Column(String(240), nullable=True)

    def __repr__(self) -> str:
        return f"<EmailReceipt(id={self.id}, ref='{self.ref}', counter={self.counter})>"
