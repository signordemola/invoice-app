from sqlalchemy import BigInteger, Column, DateTime, String, Text, func
from sqlalchemy.orm import relationship
from ..config.database import Base


class Client(Base):
    """SQLAlchemy model representing the client table."""

    __tablename__ = 'client'

    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(Text, nullable=False)
    address = Column(Text, nullable=False)
    email = Column(String(150), nullable=False, unique=True, index=True)
    phone = Column(String(25), nullable=False)
    post_addr = Column(String(20), nullable=False)

    date_created = Column(DateTime(), nullable=False,
                          server_default=func.now())

    invoices = relationship("Invoice", back_populates="client")

    def __repr__(self) -> str:
        """String representation for debugging"""
        return f"<Client(id={self.id}, name='{self.name}', email='{self.email}')>"
