"""Transaction management utilities for atomic database operations."""

from contextlib import contextmanager
from typing import Generator
import logging

from sqlalchemy.orm import Session
from sqlalchemy.exc import (
    SQLAlchemyError,
    IntegrityError,
    OperationalError,
    InvalidRequestError
)

from app.core.exceptions import (
    TransactionError,
    ConnectionError as DBConnectionError,
    ConflictError
)


logger = logging.getLogger(__name__)


@contextmanager
def transaction_scope(db: Session) -> Generator[Session, None, None]:
    """Provide transactional scope with automatic commit/rollback."""

    logger.debug("Starting database transaction")

    try:
        yield db
        db.commit()
        logger.debug("Transaction committed successfully")

    except IntegrityError as e:
        db.rollback()

        constraint_name = _extract_constraint_name(e)

        logger.error(
            "Transaction rolled back: Integrity constraint violated",
            extra={
                "error_type": "IntegrityError",
                "constraint": constraint_name,
                "original_error": str(e.orig) if hasattr(e, 'orig') else str(e)
            },
            exc_info=True
        )

        raise ConflictError(
            message=f"Operation conflicts with existing data: {constraint_name}",
            code="CONSTRAINT_VIOLATION",
            details={
                "constraint": constraint_name,
                "database_error": str(e.orig) if hasattr(e, 'orig') else str(e)
            }
        ) from e

    except OperationalError as e:
        db.rollback()

        logger.error(
            "Transaction rolled back: Database operational error",
            extra={
                "error_type": "OperationalError",
                "original_error": str(e.orig) if hasattr(e, 'orig') else str(e)
            },
            exc_info=True
        )

        raise DBConnectionError(
            message="Database connection failed or timed out",
            code="DB_CONNECTION_ERROR",
            details={
                "database_error": str(e.orig) if hasattr(e, 'orig') else str(e)
            }
        ) from e

    except InvalidRequestError as e:
        db.rollback()

        logger.error(
            "Transaction rolled back: Invalid session state",
            extra={
                "error_type": "InvalidRequestError",
                "original_error": str(e)
            },
            exc_info=True
        )

        raise TransactionError(
            message="Invalid database session operation",
            code="INVALID_SESSION_STATE",
            details={"database_error": str(e)}
        ) from e

    except SQLAlchemyError as e:
        db.rollback()

        logger.error(
            "Transaction rolled back: SQLAlchemy error",
            extra={
                "error_type": type(e).__name__,
                "original_error": str(e)
            },
            exc_info=True
        )

        raise TransactionError(
            message=f"Database error: {type(e).__name__}",
            code="DATABASE_ERROR",
            details={"database_error": str(e)}
        ) from e

    except Exception as e:
        db.rollback()

        logger.error(
            "Transaction rolled back: Unexpected error",
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e)
            },
            exc_info=True
        )

        raise


def _extract_constraint_name(error: IntegrityError) -> str:
    """Extract human-readable constraint name from IntegrityError."""

    error_msg = str(error.orig) if hasattr(error, 'orig') else str(error)

    if 'already exists' in error_msg.lower():
        if 'email' in error_msg.lower():
            return "Email address already registered"
        elif 'username' in error_msg.lower():
            return "Username already taken"
        return "Duplicate value for unique field"

    if 'foreign key' in error_msg.lower():
        if 'client_id' in error_msg.lower():
            return "Referenced client does not exist"
        elif 'invoice_id' in error_msg.lower():
            return "Referenced invoice does not exist"
        return "Referenced record does not exist"

    if 'check constraint' in error_msg.lower():
        return "Data validation failed"

    return "Database constraint violated"
