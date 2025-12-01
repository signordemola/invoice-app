from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=150)


class UserUpdate(BaseModel):
    username: str | None = Field(None, min_length=3, max_length=20)
    password: str | None = Field(None, min_length=8, max_length=150)
    is_active: bool | None = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
