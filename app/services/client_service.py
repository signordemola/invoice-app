import logging
from math import ceil
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictException, NotFoundException
from app.models.client import Client
from app.schemas.client import ClientCreate, ClientUpdate
from app.services.database import transaction_scope

logger = logging.getLogger(__name__)


def get_clients_paginated(
        db: Session,
        page: int = 1,
        limit: int = 10,
) -> dict:
    """Get paginated list of clients."""

    from app.core.exceptions import ValidationException

    if limit < 1 or limit > 100:
        raise ValidationException(
            message="Pagination limit must be between 1 and 100",
            details=[{"field": "limit", "range": "1-100"}]
        )

    skip = (page-1)*limit
    total = db.query(Client).count()

    clients = db.query(Client)\
        .order_by(Client.id.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()

    total_pages = ceil(total / limit) if total > 0 else 0

    return {
        "clients": clients,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages
        }
    }


def create_client(client_data: ClientCreate, db: Session) -> Client:
    """Add a new client."""

    with transaction_scope(db):
        existing_client = db.query(Client).filter(
            Client.email == client_data.email
        ).first()

        if existing_client:
            raise ConflictException(
                message="Email already registered",
                code="CLIENT_EMAIL_EXISTS"
            )

        new_client = Client(**client_data.model_dump())
        db.add(new_client)
        db.flush()

        return new_client


def get_client_by_id(client_id: int, db: Session) -> Client:
    """Get a single client by ID"""

    client = db.query(Client).filter(Client.id == client_id).first()

    if not client:
        raise NotFoundException(
            message=f"Client with id {client_id} not found!",
            resource="client"
        )

    return client


def update_client(client_id: int, client_data: ClientUpdate, db: Session) -> Client:
    """Update an existing client (partial update)"""

    with transaction_scope(db):
        client = db.query(Client).filter(Client.id == client_id).first()

        if not client:
            raise NotFoundException(
                message=f"Client with id {client_id} not found",
                resource="client"
            )

        update_data = client_data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(client, field, value)

        db.flush()

        return client


def delete_client(client_id: int, db: Session) -> None:
    """Delete an existing client"""

    with transaction_scope(db):
        client = db.query(Client).filter(Client.id == client_id).first()

        if not client:
            raise NotFoundException(
                message=f"Client with id {client_id} not found",
                resource="client"
            )

        db.delete(client)
