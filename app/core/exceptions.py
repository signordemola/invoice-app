"""Custom exception classes for the application."""

from typing import Optional, List, Dict, Any


class AppException(Exception):
    """Base exception class for all application exceptions."""

    def __init__(
        self,
        message: str,
        code: str,
        status_code: int = 400,
        details: Optional[List[Dict[str, Any]]] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or []
        super().__init__(self.message)


class ValidationException(AppException):
    """Raised when input validation fails."""

    def __init__(
        self,
        message: str = "Validation error",
        details: Optional[List[Dict[str, Any]]] = None
    ):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=422,
            details=details
        )


class NotFoundException(AppException):
    """Raised when a requested resource is not found."""

    def __init__(
        self,
        message: str = "Resource not found",
        resource: Optional[str] = None
    ):
        code = f"{resource.upper()}_NOT_FOUND" if resource else "NOT_FOUND"
        super().__init__(
            message=message,
            code=code,
            status_code=404
        )


class UnauthorizedException(AppException):
    """Raised when authentication fails."""

    def __init__(
        self,
        message: str = "Authentication required",
        code: str = "UNAUTHORIZED"
    ):
        super().__init__(
            message=message,
            code=code,
            status_code=401
        )


class ForbiddenException(AppException):
    """Raised when user lacks permission for an action."""

    def __init__(
        self,
        message: str = "Access forbidden",
        code: str = "FORBIDDEN"
    ):
        super().__init__(
            message=message,
            code=code,
            status_code=403
        )


class ConflictException(AppException):
    """Raised when there's a conflict (e.g., duplicate resource)."""

    def __init__(
        self,
        message: str = "Resource conflict",
        code: str = "CONFLICT"
    ):
        super().__init__(
            message=message,
            code=code,
            status_code=409
        )


class DatabaseException(AppException):
    """Raised when database operations fail."""

    def __init__(
        self,
        message: str = "Database operation failed",
        code: str = "DATABASE_ERROR"
    ):
        super().__init__(
            message=message,
            code=code,
            status_code=500
        )


class ExternalServiceException(AppException):
    """Raised when external service calls fail."""

    def __init__(
        self,
        message: str = "External service error",
        service: Optional[str] = None
    ):
        code = (
            f"{service.upper()}_ERROR"
            if service
            else "EXTERNAL_SERVICE_ERROR"
        )
        super().__init__(
            message=message,
            code=code,
            status_code=503
        )
