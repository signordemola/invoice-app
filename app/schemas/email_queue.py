from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class EmailQueueBase(BaseModel):
    field: str | None = Field(None, max_length=150)
    reference: str | None = Field(None, max_length=150)
    status: int = Field(default=0)


class EmailQueueCreate(EmailQueueBase):
    pass


class EmailQueueUpdate(BaseModel):
    field: str | None = Field(None, max_length=150)
    reference: str | None = Field(None, max_length=150)
    status: int | None = None


class EmailQueueResponse(EmailQueueBase):
    id: int
    date_created: datetime

    model_config = ConfigDict(from_attributes=True)
