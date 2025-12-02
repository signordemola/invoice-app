from math import ceil
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ....config.database import get_db
from ...dependencies import get_current_user
from ....models.client import Client
from ....models.user import User
from ....schemas.client import ClientCreate, ClientUpdate, ClientResponse

router = APIRouter()


@router.post('/', response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
def add_client(client_data: ClientCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Create a new client"""

    existing_client = db.query(Client).filter(
        Client.email == client_data.email).first()
    if existing_client:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered!"
        )

    new_client = Client(**client_data.model_dump())

    db.add(new_client)
    db.commit()
    db.refresh(new_client)

    return new_client


@router.get('/', response_model=dict)
def get_clients(page: int = 1,
                limit: int = 10,
                db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    """Get paginated list of clients"""

    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be between 1 and 100"
        )

    skip = (page - 1) * limit
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


@router.get('/{client_id}', response_model=ClientResponse)
def get_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a single client by ID"""

    client = db.query(Client).filter(Client.id == client_id).first()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client with id {client_id} not found"
        )

    return client


@router.patch('/{client_id}', response_model=ClientResponse)
def update_client(
    client_id: int,
    client_data: ClientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing client (partial update)"""

    client = db.query(Client).filter(Client.id == client_id).first()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client with id {client_id} not found"
        )

    update_data = client_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(client, field, value)

    db.commit()
    db.refresh(client)

    return client
