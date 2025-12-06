from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Text, BigInteger, Integer, DECIMAL, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from ..config.database import Base


class Expense(Base):
    __tablename__ = "expense"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(100))
    desc: Mapped[str | None] = mapped_column(Text)
    date_created: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now())
    requested_by: Mapped[str] = mapped_column(String(100))
    status: Mapped[int] = mapped_column(Integer, default=1)
    aproved_by: Mapped[str | None] = mapped_column(String(100))
    amount: Mapped[Decimal] = mapped_column(DECIMAL(15, 2))
    payment_type: Mapped[int] = mapped_column(Integer)

    def __repr__(self) -> str:
        return f"<Expense(id={self.id}, title='{self.title}', amount={self.amount})>"
