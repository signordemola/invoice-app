from fastapi import Form
from pydantic import BaseModel, Field


class LoginForm(BaseModel):
    """Form model for user login"""

    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=9)

    @classmethod
    def as_form(
        cls,
        username: str = Form(...),
        password: str = Form(...)
    ):
        return cls(username=username, password=password)


class RegisterForm(BaseModel):
    """Form model for user registration"""

    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=9)

    @classmethod
    def as_form(
        cls,
        username: str = Form(...),
        password: str = Form(...)
    ):
        return cls(username=username, password=password)
