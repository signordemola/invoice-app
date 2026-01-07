
"""Analytics API endpoints for dashboard statistics."""

import logging
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.config.database import get_db
from app.models.user import User
from app.schemas.analytics import DashboardStats
from app.services.analytics_service import get_dashboard_stats

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/dashboard",
    response_model=DashboardStats,
    status_code=status.HTTP_200_OK,
    summary="Get Dashboard Statistics",
    description="""
    Retrieve comprehensive dashboard analytics including:
    - Financial metrics (revenue, outstanding, overdue amounts)
    - Invoice status breakdown
    - Monthly revenue trends (last 12 months)
    - Top clients by revenue
    - Recent invoices and payments
    
    This endpoint requires authentication.
    """,
    responses={
        200: {
            "description": "Dashboard statistics retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "total_revenue": "150000.00",
                        "outstanding_amount": "25000.00",
                        "overdue_amount": "5000.00",
                        "total_invoices": 145,
                        "total_clients": 23,
                        "total_payments": 98,
                        "invoice_status_breakdown": [
                            {
                                "status": "paid",
                                "count": 85,
                                "total_amount": "150000.00"
                            }
                        ],
                        "monthly_revenue": [
                            {
                                "month": "2026-01",
                                "revenue": "35000.00",
                                "invoice_count": 12
                            }
                        ],
                        "top_clients": [],
                        "recent_invoices": [],
                        "recent_payments": []
                    }
                }
            }
        },
        401: {"description": "Authentication required"},
        500: {"description": "Internal server error"}
    }
)
def get_dashboard_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> DashboardStats:
    """
    Get complete dashboard analytics.

    Requires authentication. Returns aggregated business intelligence
    including financial metrics, trends, and recent activity.
    """

    logger.info(
        f"Dashboard stats requested by user: {current_user.username}",
        extra={"user_id": current_user.id}
    )

    dashboard_data = get_dashboard_stats(db)

    logger.info(
        "Dashboard stats returned successfully",
        extra={
            "user_id": current_user.id,
            "total_revenue": float(dashboard_data['total_revenue']),
            "total_invoices": dashboard_data['total_invoices']
        }
    )

    return DashboardStats(**dashboard_data)
