from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal
from datetime import datetime


class PaymentBase(BaseModel):
    client_name: str = Field(..., min_length=1, max_length=150)
    payment_mode: int = Field(..., ge=0, le=4)
    amount_paid: Decimal = Field(..., gt=0, decimal_places=2)
    payment_desc: str | None = None
    status: int = Field(..., ge=1, le=2)


class PaymentCreate(PaymentBase):
    invoice_id: int


class PaymentUpdate(BaseModel):
    client_name: str | None = Field(None, min_length=1, max_length=150)
    payment_mode: int | None = Field(None, ge=0, le=4)
    amount_paid: Decimal | None = Field(None, gt=0, decimal_places=2)
    payment_desc: str | None = None
    status: int | None = Field(None, ge=1, le=2)


class PaymentResponse(PaymentBase):
    id: int
    date_created: datetime
    balance: Decimal | None
    invoice_id: int
    view_count: int
    last_view: datetime | None

    model_config = ConfigDict(from_attributes=True)
