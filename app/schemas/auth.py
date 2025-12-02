from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Schema for login request"""
    username: str = Field(..., min_length=3, max_length=20)
    password: str = Field(..., min_length=8, max_length=150)


class TokenResponse(BaseModel):
    """OAuth2-compatible token response"""
    access_token: str
    token_type: str = "bearer"
