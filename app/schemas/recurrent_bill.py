from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal
from datetime import datetime


class RecurrentBillBase(BaseModel):
    client_id: int
    product_name: str = Field(..., min_length=1, max_length=150)
    amount_expected: Decimal = Field(..., gt=0, decimal_places=2)
    date_due: datetime
    payment_status: int = Field(default=0, ge=-1, le=2)


class RecurrentBillCreate(RecurrentBillBase):
    pass


class RecurrentBillUpdate(BaseModel):
    product_name: str | None = Field(None, min_length=1, max_length=150)
    amount_expected: Decimal | None = Field(None, gt=0, decimal_places=2)
    date_due: datetime | None = None
    payment_status: int | None = Field(None, ge=-1, le=2)


class RecurrentBillResponse(RecurrentBillBase):
    id: int
    invoice_id: int | None
    date_created: datetime
    date_updated: datetime

    model_config = ConfigDict(from_attributes=True)
