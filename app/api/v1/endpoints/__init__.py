from .auth import router as auth_router
from .clients import router as client_router
from .invoices import router as invoice_router
from .items import router as item_router
from .payments import router as payment_router

__all__ = ["auth_router", "client_router",
           "invoice_router", "item_router", "payment_router"]
