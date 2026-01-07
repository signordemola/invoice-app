from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import TypedDict, Literal, TypeGuard

from app.models.invoice import Invoice


# Constants
VAT_RATE = Decimal("7.5")
CLIENT_TYPE_STUDENT = 1
CLIENT_TYPE_INDIVIDUAL = 2
CLIENT_TYPE_CORPORATE = 3

DiscountType = Literal["fixed", "percent", "percentage"]


def is_discount_type(value: str | None) -> TypeGuard[DiscountType]:
    """Tell the type checker that a string is a valid DiscountType."""
    return value in ("fixed", "percent", "percentage")


class InvoiceTotals(TypedDict):
    """Type-safe structure for invoice calculations"""

    subtotal: Decimal
    discount: Decimal
    total: Decimal
    vat: Decimal
    vat_total: Decimal


def generate_invoice_number(invoice_id: int) -> str:
    """ Generate a unique invoice number using the database ID, Example: INV-2024-000123 """

    current_year = datetime.now().year
    return f"INV-{current_year}-{invoice_id:06d}"


def calculate_discount(
    discount_type: str | None,
    discount_value: Decimal | float | str | None,
    subtotal: Decimal | float
) -> Decimal:
    """ Calculate discount amount based on type and value """

    if not is_discount_type(discount_type) or not discount_value:
        return Decimal('0.00')

    try:
        disc_val = Decimal(str(discount_value))
        sub = Decimal(str(subtotal))

        if discount_type == "fixed":
            return min(disc_val, sub) if disc_val > 0 else Decimal('0.00')

        elif discount_type in ("percent", "percentage"):
            if 0 <= disc_val <= 100:
                return (disc_val / Decimal('100')) * sub
            return Decimal('0.00')

        else:
            return Decimal('0.00')

    except (ValueError, TypeError):
        return Decimal('0.00')


def calculate_vat(
    amount: Decimal | float,
    client_type: int,
    vat_rate: Decimal = VAT_RATE
) -> Decimal:
    """
    Calculate VAT based on client type.

    Students are VAT-exempt (return 0.00).
    Others pay standard VAT rate (7.5% in Nigeria).

    Args:
        amount: Amount to calculate VAT on
        client_type: Client type constant (STUDENT, INDIVIDUAL, CORPORATE)
        vat_rate: VAT percentage rate (default 7.5%)

    Returns:
        VAT amount as Decimal
    """
    amt = Decimal(str(amount))
    rate = vat_rate / Decimal('100')

    if client_type == CLIENT_TYPE_STUDENT:
        return Decimal('0.00')  # ← FIX: Students are VAT-exempt (not negative)
    else:
        return rate * amt


def calculate_invoice_totals(invoice: Invoice) -> InvoiceTotals:
    """Calculate all invoice totals from line items, discount, and VAT"""

    subtotal = Decimal('0.00')

    if not invoice.items:
        return {
            "subtotal": Decimal('0.00'),
            "discount": Decimal('0.00'),
            "total": Decimal('0.00'),
            "vat": Decimal('0.00'),
            "vat_total": Decimal('0.00')
        }

    for item in invoice.items:
        try:
            subtotal += Decimal(str(item.amount))
        except (ValueError, TypeError):
            continue

    discount = calculate_discount(
        invoice.disc_type,
        invoice.disc_value,
        subtotal
    )

    total_after_discount = subtotal - discount

    vat = calculate_vat(total_after_discount, invoice.client_type, VAT_RATE)

    if invoice.client_type == CLIENT_TYPE_STUDENT:
        vat_total = total_after_discount
    else:
        vat_total = total_after_discount + vat

    return {
        "subtotal": subtotal.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        "discount": discount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        "total": total_after_discount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        "vat": vat.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        "vat_total": vat_total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    }


def calculate_totals_from_values(
    disc_type: DiscountType | None,
    disc_value: Decimal | float | str | None,
    sub_total: Decimal | float,
    client_type: int
) -> tuple[Decimal, Decimal, Decimal, Decimal]:
    """ Calculate invoice totals from raw values (without Invoice object) """

    discount = calculate_discount(disc_type, disc_value, sub_total)

    total = Decimal(str(sub_total)) - discount

    vat = calculate_vat(total, client_type, VAT_RATE)

    if client_type == CLIENT_TYPE_STUDENT:
        vat_total = total
    else:
        vat_total = total + vat

    return (
        vat_total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        vat.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        discount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    )


def format_currency(amount: Decimal | float, symbol: str = "₦", include_symbol: bool = True) -> str:
    """ Format amount as currency with thousands separator """
    amt = Decimal(str(amount))
    formatted = f"{amt:,.2f}"

    if include_symbol:
        return f"{symbol}{formatted}"

    return formatted


def comma_separation(amt: Decimal | float | int | str) -> str:
    """ Format amount with comma separators"""

    if isinstance(amt, str):
        amt = Decimal(amt)
    elif isinstance(amt, int):
        amt = float(amt)

    return format_currency(amt, include_symbol=False)


def float2decimal(value: Decimal | float | str) -> Decimal:
    """ Convert float or string to Decimal, handling comma-separated values """
    if not isinstance(value, str):
        value = str(value)

    if "," in value:
        value = "".join(value.split(","))

    return Decimal(value)


def figure2decimal(value: str) -> Decimal:
    """Alias for float2decimal (backward compatible with Flask)"""
    return float2decimal(value)


def track_invoice_view(invoice: Invoice) -> None:
    """Update view tracking fields when invoice is accessed."""

    if invoice.view_count is None:
        invoice.view_count = 1
    else:
        invoice.view_count += 1

    invoice.last_view = datetime.now()


def calculate_due_date(invoice_date: datetime, payment_terms_days: int = 30) -> datetime:
    """Calculate invoice due date based on payment terms."""
    return invoice_date + timedelta(days=payment_terms_days)
