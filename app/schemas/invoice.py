from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from .item import ItemCreate, ItemResponse


class InvoiceBase(BaseModel):
    invoice_no: str = Field(..., min_length=1, max_length=30)
    purchase_no: int | None = None
    invoice_due: datetime
    client_type: int = Field(..., ge=1, le=3)
    currency: int = Field(..., ge=1, le=4)
    client_id: int
    disc_type: str | None = Field(None, max_length=10)
    disc_value: str | None = Field(None, max_length=10)
    disc_desc: str | None = None


class InvoiceCreate(InvoiceBase):
    items: list[ItemCreate] = Field(..., min_length=1)
    send_reminders: bool | None = False
    reminder_frequency: int | None = None


class InvoiceUpdate(BaseModel):
    invoice_no: str | None = Field(None, min_length=1, max_length=30)
    invoice_due: datetime | None = None
    client_type: int | None = Field(None, ge=1, le=3)
    currency: int | None = Field(None, ge=1, le=4)
    disc_type: str | None = Field(None, max_length=10)
    disc_value: str | None = Field(None, max_length=10)
    disc_desc: str | None = None
    send_reminders: bool | None = None
    reminder_frequency: int | None = None


class InvoiceResponse(InvoiceBase):
    id: int
    date_value: datetime
    view_count: int
    last_view: datetime | None
    items: list[ItemResponse] = []

    model_config = ConfigDict(from_attributes=True)
