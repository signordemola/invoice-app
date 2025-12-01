from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class EmailReceiptBase(BaseModel):
    ref: str = Field(..., min_length=1, max_length=240)
    body: str | None = Field(None, max_length=240)


class EmailReceiptCreate(EmailReceiptBase):
    counter: int = Field(default=0, ge=0)


class EmailReceiptUpdate(BaseModel):
    ref: str | None = Field(None, min_length=1, max_length=240)
    counter: int | None = Field(None, ge=0)
    body: str | None = Field(None, max_length=240)


class EmailReceiptResponse(EmailReceiptBase):
    id: int
    counter: int
    last_received: datetime

    model_config = ConfigDict(from_attributes=True)
