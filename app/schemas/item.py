from pydantic import BaseModel, Field, ConfigDict, field_validator
from decimal import Decimal


class ItemBase(BaseModel):
    item_desc: str = Field(..., min_length=1, max_length=150)
    qty: int = Field(..., ge=1)
    rate: int = Field(..., ge=0)


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    item_desc: str | None = Field(None, min_length=1, max_length=150)
    qty: int | None = Field(None, ge=1)
    rate: int | None = Field(None, ge=0)


class ItemResponse(ItemBase):
    id: int
    amount: Decimal
    invoice_id: int

    model_config = ConfigDict(from_attributes=True)
