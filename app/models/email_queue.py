from datetime import datetime
from sqlalchemy import Column, String, BigInteger, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from ..config.database import Base


class EmailQueue(Base):
    __tablename__ = "email_queue"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    field: Mapped[str | None] = mapped_column(String(150))
    reference: Mapped[str | None] = mapped_column(String(150))
    date_created: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now())
    status: Mapped[int] = mapped_column(Integer, default=0)

    def __repr__(self) -> str:
        return f"<EmailQueue(id={self.id}, reference='{self.reference}', status={self.status})>"
