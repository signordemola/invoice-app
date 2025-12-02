from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, ConfigDict


class ClientBase(BaseModel):
    """Shared fields for client operations"""

    name: str = Field(..., min_length=1, max_length=150)
    address: str = Field(..., min_length=1)
    email: EmailStr
    phone: str = Field(..., min_length=3, max_length=25)
    post_addr: str = Field(..., min_length=1, max_length=20)


class ClientCreate(ClientBase):
    """Schema for creating a new client (POST /clients)"""

    pass


class ClientUpdate(BaseModel):
    """Schema for updating an existing client (PATCH /clients/{id})"""

    name: str | None = Field(None, min_length=1, max_length=150)
    address: str | None = Field(None, min_length=1)
    email: EmailStr | None = None
    phone: str | None = Field(None, min_length=3, max_length=25)
    post_addr: str | None = Field(None, min_length=1, max_length=20)


class ClientResponse(ClientBase):
    """Schema for returning client data (GET /clients, GET /clients/{id})"""

    id: int
    date_created: datetime
    model_config = ConfigDict(from_attributes=True)
