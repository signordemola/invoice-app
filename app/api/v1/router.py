from fastapi import APIRouter

from .endpoints import auth_router
from .endpoints import client_router


api_router = APIRouter()

api_router.include_router(auth_router, prefix='/auth', tags=["Authentication"])
api_router.include_router(client_router, prefix='/client', tags=["Clients"])
