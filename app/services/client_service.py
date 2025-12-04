from math import ceil
from unittest import skip
from sqlalchemy.orm import Session

from app.models.client import Client
from app.schemas.client import ClientCreate, ClientUpdate


class ClientServiceError(Exception):
    """Base exception for client service errors"""
    pass


class ClientNotFoundError(ClientServiceError):
    """Raised when a client is not found"""
    pass


class ClientEmailExistsError(ClientServiceError):
    """Raised when attempting to use an email that already exists"""
    pass


def get_clients_paginated(
        db: Session,
        page: int = 1,
        limit: int = 10,
) -> dict:
    """Get paginated list of clients."""

    if limit < 1 or limit > 100:
        raise ValueError("Limit must be between 1 and 100!")

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

    existing_client = db.query(Client).filter(
        Client.email == client_data.email
    ).first()

    if existing_client:
        raise ClientEmailExistsError("Email already registered!")

    new_client = Client(**client_data.model_dump())

    db.add(new_client)
    db.commit()
    db.refresh(new_client)

    return new_client


def get_client_by_id(client_id: int, db: Session) -> Client:
    """Get a single client by ID"""

    client = db.query(Client).filter(Client.id == client_id).first()

    if not client:
        raise ClientNotFoundError(f"Client with id {client_id} not found!")

    return client


def update_client(client_id: int, client_data: ClientUpdate, db: Session) -> Client:
    """Update an existing client (partial update)"""

    client = db.query(Client).filter(Client.id == client_id).first()

    if not client:
        raise ClientNotFoundError(f"Client with id {client_id} not found")

    update_data = client_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(client, field, value)

    db.commit()
    db.refresh(client)

    return client


def delete_client(client_id: int, db: Session) -> None:
    """Delete an existing client"""

    client = db.query(Client).filter(Client.id == client_id).first()

    if not client:
        raise ClientNotFoundError(f"Client with id {client_id} not found!")

    db.delete(client)
    db.commit()
