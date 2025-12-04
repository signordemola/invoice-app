import os
from typing import Literal
from dotenv import load_dotenv
from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    """Application settings using pydantic"""

    # Application
    APP_NAME: str = Field(default="Invoice Management System")
    APP_VERSION: str = Field(default="1.0.0")
    API_VERSION: str = Field(default="/api/v1/")
    DEBUG: bool = Field(default=False)
    ENV: str = Field(default="development")
    PORT: int = Field(default=8000)

    # Database
    DATABASE_URL: str = Field(default='sqlite:///bot.db')

    # CORS
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:8080")

    # JWT Authentication
    SECRET_KEY: str = Field(default="dev-secret-key-change-in-production")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)

    # Cookie Settings
    COOKIE_NAME: str = Field(default="access_token")
    COOKIE_HTTPONLY: bool = Field(default=True)
    COOKIE_SECURE: bool = Field(default=False)
    COOKIE_SAMESITE: Literal["lax", "strict", "none"] = Field(default="lax")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    @computed_field
    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string"""
        if self.ENV.lower() == "production":
            return ["https://yourdomain.com"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @computed_field
    @property
    def cookie_max_age(self) -> int:
        """Calculate cookie max age in seconds from token expiration minutes"""
        return self.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if self.ENV == "production":
            if self.SECRET_KEY == "dev-secret-key-change-in-production":
                raise ValueError(
                    "SECRET_KEY must be set in production! "
                    "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
                )

            if not self.COOKIE_SECURE:
                raise ValueError(
                    "COOKIE_SECURE must be True in production! "
                    "Set COOKIE_SECURE=True in your .env file."
                )


settings = Settings()
