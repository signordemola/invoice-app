from sqlalchemy import Column, String, Text, BigInteger, Integer, DECIMAL, DateTime, func
from app.config.database import Base


class Expense(Base):
    __tablename__ = "expense"

    id = Column(BigInteger, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    desc = Column(Text, nullable=True)
    date_created = Column(DateTime, nullable=False, server_default=func.now())
    requested_by = Column(String(100), nullable=False)
    status = Column(Integer, nullable=False, default=1)
    aproved_by = Column(String(100), nullable=True)
    amount = Column(DECIMAL(15, 2), nullable=False)
    payment_type = Column(Integer, nullable=False)

    def __repr__(self) -> str:
        return f"<Expense(id={self.id}, title='{self.title}', amount={self.amount})>"
