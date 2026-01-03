from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime

from ..models.invoice import InvoiceStatus
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
    invoice_due: datetime | None = None
    currency: int | None = Field(None, ge=1, le=4)
    status: InvoiceStatus | None = None
    disc_type: Literal["fixed", "percent", "percentage"] | None = None
    disc_value: str | None = Field(None, max_length=10)
    disc_desc: str | None = Field(None, max_length=500)
    send_reminders: bool | None = None
    reminder_frequency: int | None = Field(
        None,
        ge=1,
        le=7,
        description="Days between reminders (1-7)"
    )


class InvoiceResponse(InvoiceBase):
    id: int
    date_value: datetime
    status: InvoiceStatus
    view_count: int
    last_view: datetime | None
    items: list[ItemResponse] = []

    model_config = ConfigDict(from_attributes=True)


class PaginationInfo(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int


class InvoicePaginatedResponse(BaseModel):
    invoices: list[InvoiceResponse]
    pagination: PaginationInfo


class InvoiceStatusUpdate(BaseModel):
    status: InvoiceStatus = Field(...,
                                  description="New status for an existing invoice")
