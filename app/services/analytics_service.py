"""Analytics service for dashboard statistics and business intelligence."""

from datetime import timedelta
from decimal import Decimal
import logging
from sqlalchemy import func, and_, or_, case, extract
from sqlalchemy.orm import Session, joinedload

from app.models.client import Client
from app.models.invoice import Invoice, InvoiceStatus
from app.models.payment import Payment, PaymentStatus
from app.utils.datetime_utils import get_current_timezone


logger = logging.getLogger(__name__)


def get_total_revenue(db: Session) -> Decimal:
    """
    Calculate total revenue from all paid invoices.

    Returns:
        Total amount from invoices with status = PAID
    """

    from app.utils.invoice_utils import calculate_invoice_totals

    paid_invoices = db.query(Invoice).filter(
        Invoice.status == InvoiceStatus.PAID
    ).all()

    total = Decimal('0.00')
    for invoice in paid_invoices:
        totals = calculate_invoice_totals(invoice)
        total += totals['vat_total']

    logger.info(f"Total revenue calculated: {total}")
    return total


def get_outstanding_amount(db: Session) -> Decimal:
    """
    Calculate total outstanding amount from unpaid invoices.

    Includes: SENT, VIEWED, PARTIALLY_PAID, OVERDUE statuses
    """

    from app.utils.invoice_utils import calculate_invoice_totals

    unpaid_statuses = [
        InvoiceStatus.SENT,
        InvoiceStatus.VIEWED,
        InvoiceStatus.PARTIALLY_PAID,
        InvoiceStatus.OVERDUE
    ]

    unpaid_invoices = db.query(Invoice).filter(
        Invoice.status.in_(unpaid_statuses)
    ).all()

    total_outstanding = Decimal('0.00')

    for invoice in unpaid_invoices:
        totals = calculate_invoice_totals(invoice)
        invoice_total = totals['vat_total']

        total_paid = sum(
            p.amount_paid for p in invoice.payments
            if p.status != PaymentStatus.CANCELLED
        )

        remaining = invoice_total - Decimal(str(total_paid))
        total_outstanding += remaining

    logger.info(f"Outstanding amount calculated: {total_outstanding}")
    return total_outstanding


def get_overdue_amount(db: Session) -> Decimal:
    """
    Calculate total overdue amount from invoices past due date.

    Only counts invoices with OVERDUE status.
    """

    from app.utils.invoice_utils import calculate_invoice_totals

    overdue_invoices = db.query(Invoice).filter(
        Invoice.status == InvoiceStatus.OVERDUE
    ).all()

    total_overdue = Decimal('0.00')

    for invoice in overdue_invoices:
        totals = calculate_invoice_totals(invoice)
        invoice_total = totals['vat_total']

        total_paid = sum(
            p.amount_paid for p in invoice.payments
            if p.status != PaymentStatus.CANCELLED
        )

        remaining = invoice_total - Decimal(str(total_paid))
        total_overdue += remaining

    logger.info(f"Overdue amount calculated: {total_overdue}")
    return total_overdue


def get_invoice_status_breakdown(db: Session) -> list[dict]:
    """
    Get count and total amount for each invoice status.

    Returns:
        List of dicts with status, count, and total_amount
    """

    from app.utils.invoice_utils import calculate_invoice_totals

    invoices_by_status = db.query(Invoice).all()

    status_map = {}

    for invoice in invoices_by_status:
        status = invoice.status.value

        if status not in status_map:
            status_map[status] = {
                'status': status,
                'count': 0,
                'total_amount': Decimal('0.00')
            }

        status_map[status]['count'] += 1

        totals = calculate_invoice_totals(invoice)
        status_map[status]['total_amount'] += totals['vat_total']

    result = list(status_map.values())
    logger.info(f"Status breakdown calculated: {len(result)} statuses")
    return result


def get_entity_counts(db: Session) -> dict:
    """
    Get counts of key entities.

    Returns:
        Dict with total_invoices, total_clients, total_payments
    """

    counts = {
        'total_invoices': db.query(Invoice).count(),
        'total_clients': db.query(Client).count(),
        'total_payments': db.query(Payment).filter(
            Payment.status != PaymentStatus.CANCELLED
        ).count()
    }

    logger.info(f"Entity counts: {counts}")
    return counts


def get_monthly_revenue(db: Session, months: int = 12) -> list[dict]:
    """
    Calculate revenue by month for the past N months.

    Args:
        db: Database session
        months: Number of months to look back (default 12)

    Returns:
        List of dicts with month, revenue, invoice_count
    """

    from app.utils.invoice_utils import calculate_invoice_totals

    current_date = get_current_timezone("Africa/Lagos")
    start_date = current_date - timedelta(days=months * 30)

    invoices = db.query(Invoice).filter(
        and_(
            Invoice.status == InvoiceStatus.PAID,
            Invoice.date_value >= start_date
        )
    ).order_by(Invoice.date_value.asc()).all()

    monthly_data = {}

    for invoice in invoices:
        month_key = invoice.date_value.strftime('%Y-%m')

        if month_key not in monthly_data:
            monthly_data[month_key] = {
                'month': month_key,
                'revenue': Decimal('0.00'),
                'invoice_count': 0
            }

        totals = calculate_invoice_totals(invoice)
        monthly_data[month_key]['revenue'] += totals['vat_total']
        monthly_data[month_key]['invoice_count'] += 1

    result = sorted(monthly_data.values(), key=lambda x: x['month'])

    logger.info(f"Monthly revenue calculated for {len(result)} months")
    return result


def get_top_clients(db: Session, limit: int = 10) -> list[dict]:
    """
    Get top clients by total revenue.

    Args:
        db: Database session
        limit: Number of top clients to return

    Returns:
        List of dicts with client_id, client_name, total_revenue, 
        invoice_count, last_invoice_date
    """

    from app.utils.invoice_utils import calculate_invoice_totals

    invoices = db.query(Invoice).options(
        joinedload(Invoice.client)
    ).filter(
        Invoice.status == InvoiceStatus.PAID
    ).all()

    client_map = {}

    for invoice in invoices:
        client_id = invoice.client_id

        if client_id not in client_map:
            client_map[client_id] = {
                'client_id': client_id,
                'client_name': invoice.client.name,
                'total_revenue': Decimal('0.00'),
                'invoice_count': 0,
                'last_invoice_date': invoice.date_value
            }

        totals = calculate_invoice_totals(invoice)
        client_map[client_id]['total_revenue'] += totals['vat_total']
        client_map[client_id]['invoice_count'] += 1

        if invoice.date_value > client_map[client_id]['last_invoice_date']:
            client_map[client_id]['last_invoice_date'] = invoice.date_value

    sorted_clients = sorted(
        client_map.values(),
        key=lambda x: x['total_revenue'],
        reverse=True
    )[:limit]

    logger.info(f"Top {len(sorted_clients)} clients calculated")
    return sorted_clients


def get_recent_invoices(db: Session, limit: int = 5) -> list[Invoice]:
    """
    Get most recent invoices with client relationship loaded.

    Args:
        db: Database session
        limit: Number of invoices to return

    Returns:
        List of Invoice objects with client data
    """

    invoices = db.query(Invoice).options(
        joinedload(Invoice.client)
    ).order_by(
        Invoice.date_value.desc()
    ).limit(limit).all()

    logger.info(f"Retrieved {len(invoices)} recent invoices")
    return invoices


def get_recent_payments(db: Session, limit: int = 5) -> list[Payment]:
    """
    Get most recent payments with invoice relationship loaded.

    Args:
        db: Database session
        limit: Number of payments to return

    Returns:
        List of Payment objects with invoice data
    """

    payments = db.query(Payment).options(
        joinedload(Payment.invoice)
    ).filter(
        Payment.status != PaymentStatus.CANCELLED
    ).order_by(
        Payment.payment_date.desc()
    ).limit(limit).all()

    logger.info(f"Retrieved {len(payments)} recent payments")
    return payments


def get_dashboard_stats(db: Session) -> dict:
    """
    Orchestrate all analytics queries and return complete dashboard data.

    This is the main entry point for dashboard analytics. It calls all
    individual metric functions and aggregates results into a single response.

    Args:
        db: Database session

    Returns:
        Dict containing all dashboard statistics ready for API response

    Raises:
        Exception: If any critical calculation fails
    """
    
    logger.info("Starting dashboard stats calculation")

    try:
        # Financial metrics (parallel-safe calculations)
        total_revenue = get_total_revenue(db)
        outstanding_amount = get_outstanding_amount(db)
        overdue_amount = get_overdue_amount(db)

        # Entity counts
        counts = get_entity_counts(db)

        # Status breakdown
        status_breakdown = get_invoice_status_breakdown(db)

        # Time series data
        monthly_revenue = get_monthly_revenue(db, months=12)

        # Top performers
        top_clients = get_top_clients(db, limit=10)

        # Recent activity
        recent_invoices_raw = get_recent_invoices(db, limit=5)
        recent_payments_raw = get_recent_payments(db, limit=5)

        # Transform recent invoices to summary format
        from app.utils.invoice_utils import calculate_invoice_totals

        recent_invoices = []
        for invoice in recent_invoices_raw:
            totals = calculate_invoice_totals(invoice)
            recent_invoices.append({
                'id': invoice.id,
                'invoice_no': invoice.invoice_no,
                'client_name': invoice.client.name,
                'date_value': invoice.date_value,
                'status': invoice.status.value,
                'total_amount': totals['vat_total']
            })

        # Transform recent payments to summary format
        recent_payments = []
        for payment in recent_payments_raw:
            recent_payments.append({
                'id': payment.id,
                'client_name': payment.client_name,
                'amount_paid': payment.amount_paid,
                'payment_date': payment.payment_date,
                'invoice_no': payment.invoice.invoice_no if payment.invoice else 'N/A'
            })

        # Aggregate all data
        dashboard_data = {
            # Financial metrics
            'total_revenue': total_revenue,
            'outstanding_amount': outstanding_amount,
            'overdue_amount': overdue_amount,

            # Counts
            'total_invoices': counts['total_invoices'],
            'total_clients': counts['total_clients'],
            'total_payments': counts['total_payments'],

            # Breakdowns
            'invoice_status_breakdown': status_breakdown,

            # Time series
            'monthly_revenue': monthly_revenue,

            # Top performers
            'top_clients': top_clients,

            # Recent activity
            'recent_invoices': recent_invoices,
            'recent_payments': recent_payments
        }

        logger.info("Dashboard stats calculation completed successfully")
        return dashboard_data

    except Exception as e:
        logger.error(
            f"Error calculating dashboard stats: {str(e)}", exc_info=True)
        raise
