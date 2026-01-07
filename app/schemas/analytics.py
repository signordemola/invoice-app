"""Analytics response schemas for dashboard data."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class InvoiceStatusCount(BaseModel):
    """Count of invoices by status."""

    status: str = Field(..., description="Invoice status")
    count: int = Field(..., ge=0, description="Number of invoices")
    total_amount: Decimal = Field(...,
                                  description="Total amount for this status")


class MonthlyRevenue(BaseModel):
    """Revenue data for a single month."""

    month: str = Field(..., description="Month in YYYY-MM format")
    revenue: Decimal = Field(..., ge=0,
                             description="Total revenue for the month")
    invoice_count: int = Field(..., ge=0, description="Number of invoices")


class TopClient(BaseModel):
    """Client revenue summary."""

    client_id: int
    client_name: str
    total_revenue: Decimal = Field(..., ge=0)
    invoice_count: int = Field(..., ge=0)
    last_invoice_date: Optional[datetime] = None


class RecentInvoiceSummary(BaseModel):
    """Simplified invoice data for recent activity."""

    id: int
    invoice_no: str
    client_name: str
    date_value: datetime
    status: str
    total_amount: Decimal

    model_config = ConfigDict(from_attributes=True)


class RecentPaymentSummary(BaseModel):
    """Simplified payment data for recent activity."""

    id: int
    client_name: str
    amount_paid: Decimal
    payment_date: datetime
    invoice_no: str

    model_config = ConfigDict(from_attributes=True)


class DashboardStats(BaseModel):
    """Complete dashboard statistics response."""

    total_revenue: Decimal = Field(..., description="Total paid invoices")
    outstanding_amount: Decimal = Field(..., description="Unpaid invoices")
    overdue_amount: Decimal = Field(..., description="Overdue invoices")

    total_invoices: int = Field(..., ge=0)
    total_clients: int = Field(..., ge=0)
    total_payments: int = Field(..., ge=0)

    invoice_status_breakdown: list[InvoiceStatusCount]

    monthly_revenue: list[MonthlyRevenue]

    top_clients: list[TopClient]

    recent_invoices: list[RecentInvoiceSummary]
    recent_payments: list[RecentPaymentSummary]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_revenue": "150000.00",
                "outstanding_amount": "25000.00",
                "overdue_amount": "5000.00",
                "total_invoices": 145,
                "total_clients": 23,
                "total_payments": 98,
                "invoice_status_breakdown": [
                    {"status": "paid", "count": 85, "total_amount": "150000.00"},
                    {"status": "sent", "count": 30, "total_amount": "20000.00"}
                ],
                "monthly_revenue": [
                    {"month": "2026-01", "revenue": "35000.00", "invoice_count": 12}
                ],
                "top_clients": [
                    {
                        "client_id": 1,
                        "client_name": "Acme Corp",
                        "total_revenue": "45000.00",
                        "invoice_count": 15,
                        "last_invoice_date": "2026-01-15T10:00:00"
                    }
                ],
                "recent_invoices": [],
                "recent_payments": []
            }
        }
    )
