from sqlalchemy import Column, String, BigInteger, Integer, DateTime, func
from app.config.database import Base


class EmailQueue(Base):
    __tablename__ = "email_queue"

    id = Column(BigInteger, primary_key=True, index=True)
    field = Column(String(150), nullable=True)
    reference = Column(String(150), nullable=True)
    date_created = Column(DateTime, nullable=False, server_default=func.now())
    status = Column(Integer, nullable=False, default=0)

    def __repr__(self) -> str:
        return f"<EmailQueue(id={self.id}, reference='{self.reference}', status={self.status})>"
