from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal
from datetime import datetime

from ..models.payment import PaymentMode, PaymentStatus


class PaymentBase(BaseModel):
    client_name: str = Field(..., min_length=1, max_length=150)
    payment_mode: PaymentMode
    payment_date: datetime
    amount_paid: Decimal = Field(..., gt=0, decimal_places=2)
    reference_number: str | None = Field(None, max_length=100)
    payment_desc: str | None = None
    status: PaymentStatus


class PaymentCreate(PaymentBase):
    invoice_id: int


class PaymentUpdate(BaseModel):
    client_name: str | None = Field(None, min_length=1, max_length=150)
    payment_mode: PaymentMode | None = None
    amount_paid: Decimal | None = Field(None, gt=0, decimal_places=2)
    payment_desc: str | None = None
    status: PaymentStatus | None = None


class PaymentResponse(PaymentBase):
    id: int
    date_created: datetime
    invoice_id: int
    view_count: int
    last_view: datetime | None

    model_config = ConfigDict(from_attributes=True)
