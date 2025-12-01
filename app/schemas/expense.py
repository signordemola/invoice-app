from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal
from datetime import datetime


class ExpenseBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    desc: str | None = None
    requested_by: str = Field(..., min_length=1, max_length=100)
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    payment_type: int = Field(..., ge=1, le=5)


class ExpenseCreate(ExpenseBase):
    status: int = Field(default=1, ge=1, le=3)
    aproved_by: str | None = None


class ExpenseUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=100)
    desc: str | None = None
    amount: Decimal | None = Field(None, gt=0, decimal_places=2)
    status: int | None = Field(None, ge=1, le=3)
    aproved_by: str | None = None
    payment_type: int | None = Field(None, ge=1, le=5)


class ExpenseResponse(ExpenseBase):
    id: int
    date_created: datetime
    status: int
    aproved_by: str | None

    model_config = ConfigDict(from_attributes=True)
