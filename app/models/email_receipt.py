from datetime import datetime
from sqlalchemy import String, BigInteger, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from ..config.database import Base


class EmailReceipt(Base):
    __tablename__ = "email_receipt_count"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    ref: Mapped[str] = mapped_column(String(240), index=True)
    counter: Mapped[int] = mapped_column(BigInteger, default=0)
    last_received: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now())
    body: Mapped[str | None] = mapped_column(String(240))

    def __repr__(self) -> str:
        return f"<EmailReceipt(id={self.id}, ref='{self.ref}', counter={self.counter})>"
