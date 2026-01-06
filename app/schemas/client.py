from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, ConfigDict, field_validator
from email_validator import validate_email, EmailNotValidError


class ClientBase(BaseModel):
    """Shared fields for client operations"""

    name: str = Field(..., min_length=1, max_length=150)
    address: str = Field(..., min_length=1)
    email: EmailStr
    phone: str = Field(..., min_length=3, max_length=25)
    post_addr: str = Field(..., min_length=1, max_length=20)

    @field_validator('email')
    @classmethod
    def validate_email(cls, value: str) -> str:
        """Validate email deliverability."""

        try:
            validated = validate_email(
                value, check_deliverability=True, allow_smtputf8=True
            )
            return validated.normalized
        except EmailNotValidError as e:
            raise ValueError(f"Invalid email address: {str(e)}") from e


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

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        """Validate and normalize email if provided"""

        if value is None:
            return None

        try:
            validated = validate_email(
                value, check_deliverability=True, allow_smtputf8=True)
            return validated.normalized
        except EmailNotValidError as e:
            raise ValueError(f"Invalid email address: {str(e)}")


class ClientResponse(ClientBase):
    """Schema for returning client data (GET /clients, GET /clients/{id})"""

    id: int
    date_created: datetime
    model_config = ConfigDict(from_attributes=True)


class Pagination(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int


class ClientsResponse(BaseModel):
    clients: list[ClientResponse]
    pagination: Pagination
