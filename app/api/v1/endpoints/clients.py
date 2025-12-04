from math import ceil
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.services.client_service import ClientEmailExistsError, ClientNotFoundError, create_client, delete_client, get_client_by_id, get_clients_paginated, update_client

from ....config.database import get_db
from ...dependencies import get_current_user
from ....models.client import Client
from ....models.user import User
from ....schemas.client import ClientCreate, ClientUpdate, ClientResponse, ClientsResponse

router = APIRouter()


@router.post('/', response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
def add_client_route(client_data: ClientCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Create a new client"""

    try:
        new_client = create_client(client_data, db)
        return new_client

    except ClientEmailExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )


@router.get('/', response_model=ClientsResponse)
def get_clients_route(page: int = 1,
                      limit: int = 10,
                      db: Session = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    """Get paginated list of clients"""

    try:
        result = get_clients_paginated(db, page, limit)
        return result

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )


@router.get('/{client_id}', response_model=ClientResponse)
def get_client_route(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a single client by ID"""

    try:
        client = get_client_by_id(client_id, db)
        return client

    except ClientNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )


@router.patch('/{client_id}', response_model=ClientResponse)
def update_client_route(
    client_id: int,
    client_data: ClientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing client (partial update)"""

    try:
        updated_client = update_client(client_id, client_data, db)
        return updated_client

    except ClientNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete('/{client_id}', status_code=status.HTTP_204_NO_CONTENT)
def delet_client_route(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a client"""

    try:
        delete_client(client_id, db)
        return None

    except ClientNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
