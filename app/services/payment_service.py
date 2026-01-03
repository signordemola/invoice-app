"""Payment service for handling payment business logic and database operations."""

from sqlalchemy.orm import Session


class PaymentServiceError(Exception):
    """Base exception for payment service errors"""
    pass


class PaymentNotFoundError(PaymentServiceError):
    """Raised when a payment is not found"""
    pass


class InvalidPaymentDataError(PaymentServiceError):
    """Raised when payment data is invalid (e.g., negative amount, future dates)"""
    pass


class InvoiceNotFoundError(PaymentServiceError):
    """Raised when the specified invoice doesn't exist"""
    pass


class DuplicatePaymentError(PaymentServiceError):
    """Raised when attempting to create a duplicate payment (same reference number)"""
    pass
