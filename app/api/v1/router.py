from fastapi import APIRouter

from .endpoints import auth_router, client_router, invoice_router, item_router, payment_router, analytics_router


api_router = APIRouter()

api_router.include_router(auth_router, prefix='/auth', tags=["Authentication"])
api_router.include_router(client_router, prefix='/client', tags=["Clients"])
api_router.include_router(
    invoice_router, prefix='/invoices', tags=["Invoices"])
api_router.include_router(item_router, prefix='/items', tags=["Items"])
api_router.include_router(
    payment_router, prefix='/payments', tags=["Payments"])
api_router.include_router(analytics_router, prefix='/analytics', tags=["Analytics"])

