from contextlib import asynccontextmanager
from typing import AsyncIterator
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.api.exception_handler import app_exception_handler, unhandled_exception_handler, validation_exception_handler
from app.config.database import init_db
from app.core.exceptions import AppException


from .config import settings
from .api.v1 import api_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan with database and task queue initialization."""
    
    init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    docs_url=settings.DOCS_URL,
    redoc_url=settings.REDOC_URL,
    lifespan=lifespan
)

app.add_exception_handler(AppException, app_exception_handler) # type: ignore[arg-type]
app.add_exception_handler(RequestValidationError, validation_exception_handler) # type: ignore[arg-type]
app.add_exception_handler(Exception, unhandled_exception_handler)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["yourdomain.com"] if settings.ENV == "production" else ["*"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get('/')
def root() -> dict:
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": settings.API_VERSION
    }


@app.get("/health")
def health_check():
    """Health check endpoint for monitoring and load balancers."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.ENV
    }


# @app.get("/metrics")
# def metrics():
#     """Prometheus metrics endpoint."""
#     return metrics_endpoint()


# API ENDPOINTS
app.include_router(api_router, prefix=settings.API_VERSION)
