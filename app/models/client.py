from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import BigInteger, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..config.database import Base

if TYPE_CHECKING:
    from .invoice import Invoice


class Client(Base):
    """SQLAlchemy model representing the client table."""

    __tablename__ = 'client'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(Text, index=True)
    address: Mapped[str] = mapped_column(Text)
    email: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(25), index=True)
    post_addr: Mapped[str] = mapped_column(String(20))
    date_created: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now())

    invoices: Mapped[list["Invoice"]] = relationship(
        back_populates="client",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    def __repr__(self) -> str:
        """String representation for debugging"""
        return f"<Client(id={self.id}, name='{self.name}', email='{self.email}')>"
