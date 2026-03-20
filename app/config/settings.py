import os
from typing import Literal, Optional
from dotenv import load_dotenv
from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()

LOCAL_ALLOWED_HOSTS = "localhost,127.0.0.1,::1,0.0.0.0,testserver"


class Settings(BaseSettings):
    """Application settings using pydantic"""

    # Application
    APP_NAME: str = Field(default="Invoice Management System")
    APP_VERSION: str = Field(default="1.0.0")
    API_VERSION: str = Field(default="/api/v1")
    DEBUG: bool = Field(default=False)
    ENV: str = Field(default="development")
    PORT: int = Field(default=8000)

    # Documentation URLs (new section)
    DOCS_URL: str = Field(default="/docs")
    REDOC_URL: str = Field(default="/redoc")

    # Database
    DATABASE_URL: str = Field(default='sqlite:///bot.db')
    POOL_SIZE: int = Field(10, validation_alias="POOL_SIZE")
    MAX_OVERFLOW: int = Field(20, validation_alias="MAX_OVERFLOW")
    POOL_TIMEOUT: int = Field(40, validation_alias="POOL_TIMEOUT")
    POOL_RECYCLE: int = Field(1800, validation_alias="POOL_RECYCLE")
    CONNECT_TIMEOUT: int = Field(10, validation_alias="DB_CONNECT_TIMEOUT")
    UPSTASH_REDIS_BROKER_URL: Optional[str] = Field(
        None,
        validation_alias="UPSTASH_REDIS_BROKER_URL"
    )
    UPSTASH_REDIS_BACKEND_URL: Optional[str] = Field(
        None,
        validation_alias="UPSTASH_REDIS_BACKEND_URL"
    )
    SENTRY_DSN: Optional[str] = Field(
        None,
        validation_alias="SENTRY_DSN"
    )

    # Email Settings
    RESEND_API_KEY: str = Field(...,
                                description="Resend API key for sending emails")
    EMAIL_FROM_ADDRESS: str = Field(default="noreply@yourdomain.com")
    EMAIL_FROM_NAME: str = Field(default="Invoice Management System")
    EMAIL_VERIFICATION_TOKEN_EXPIRATION_HOURS: int = Field(
        24,
        validation_alias="EMAIL_VERIFICATION_TOKEN_EXPIRATION_HOURS"
    )
    PASSWORD_RESET_TOKEN_EXPIRATION_MINUTES: int = Field(
        30,
        validation_alias="PASSWORD_RESET_TOKEN_EXPIRATION_MINUTES"
    )

    # CORS
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:8080")

    # Exemption for specific IPs (comma-separated)
    RATE_LIMIT_EXEMPT_IPS: Optional[str] = Field(
        None,
        validation_alias="RATE_LIMIT_EXEMPT_IPS"
    )

    # JWT Authentication
    SECRET_KEY: str = Field(default="dev-secret-key-change-in-production")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=60, validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    ACCESS_TOKEN_EXPIRATION: int = Field(
        60, validation_alias="ACCESS_TOKEN_EXPIRATION")
    REFRESH_TOKEN_EXPIRATION: int = Field(
        60 * 24 * 7, validation_alias="REFRESH_TOKEN_EXPIRATION")

    # Cookie Settings
    COOKIE_NAME: str = Field(default="access_token")
    REFRESH_COOKIE_NAME: str = Field(default="refresh_token")
    CSRF_COOKIE_NAME: str = Field(default="csrf_token")
    CSRF_HEADER_NAME: str = Field(default="X-CSRF-Token")
    COOKIE_HTTPONLY: bool = Field(default=True)
    COOKIE_SECURE: bool = Field(default=True)
    COOKIE_SAMESITE: Literal["lax", "strict", "none"] = Field(default="strict")
    ALLOWED_HOSTS: str = Field(default=LOCAL_ALLOWED_HOSTS)

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
    def access_cookie_max_age(self) -> int:
        """Calculate access-token cookie max age in seconds."""
        return self.ACCESS_TOKEN_EXPIRATION * 60

    @computed_field
    @property
    def refresh_cookie_max_age(self) -> int:
        """Calculate refresh-token cookie max age in seconds."""
        return self.REFRESH_TOKEN_EXPIRATION * 60

    @computed_field
    @property
    def cookie_max_age(self) -> int:
        """Backward-compatible access-token cookie max age."""
        return self.access_cookie_max_age

    @computed_field
    @property
    def allowed_hosts_list(self) -> list[str]:
        """Parse allowed hosts from a comma-separated string."""
        return [host.strip() for host in self.ALLOWED_HOSTS.split(",") if host.strip()]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        env = self.ENV.lower()
        is_local_env = env in {"development", "dev", "local", "test"}

        if not is_local_env:
            if self.SECRET_KEY == "dev-secret-key-change-in-production":
                raise ValueError(
                    "SECRET_KEY must be set outside local development! "
                    "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
                )

            if len(self.SECRET_KEY) < 32:
                raise ValueError(
                    "SECRET_KEY must be at least 32 characters outside local development."
                )

            if not self.COOKIE_SECURE:
                raise ValueError(
                    "COOKIE_SECURE must be True outside local development! "
                    "Set COOKIE_SECURE=True in your .env file."
                )

            if self.ALLOWED_HOSTS == LOCAL_ALLOWED_HOSTS:
                raise ValueError(
                    "ALLOWED_HOSTS must be configured outside local development."
                )


def get_settings() -> Settings:
    return Settings()


settings = get_settings()
