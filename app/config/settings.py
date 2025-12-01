import os
from dotenv import load_dotenv
from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    """Application settings using pydantic"""

    # Application
    APP_NAME: str = Field(default="Invoice Management System")
    APP_VERSION: str = Field(default="1.0.0")
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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    @computed_field(return_type=list[str])
    def cors_origins_list(self):
        """Parse CORS origins from comma-separated string"""
        if self.ENV.lower() == "production":
            return ["https://yourdomain.com"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if self.ENV == "production":
            if self.SECRET_KEY == "dev-secret-key-change-in-production":
                raise ValueError(
                    "SECRET_KEY must be set in production! "
                    "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
                )


settings = Settings()
