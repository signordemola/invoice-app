from decimal import Decimal


def comma_separation(amt: Decimal | float | int | str) -> str:
    """
    Format amount with thousand separators and 2 decimal places.

    Examples:
        >>> comma_separation(1234.56)
        '1,234.56'
        >>> comma_separation(Decimal('1234567.89'))
        '1,234,567.89'
    """
    amount = float(amt)
    return f"{amount:,.2f}"


def float2decimal(value: Decimal | float | str) -> Decimal:
    """Convert float or string to Decimal, handling comma-separated values"""
    if not isinstance(value, str):
        value = str(value)

    # Remove commas if present
    if "," in value:
        value = "".join(value.split(","))

    return Decimal(value)


def figure2decimal(value: str) -> Decimal:
    """Alias for float2decimal"""
    return float2decimal(value)


def format_currency(amount: Decimal | float, symbol: str = "₦", include_symbol: bool = True) -> str:
    """
    Format amount as currency with symbol.

    Examples:
        >>> format_currency(1234.56)
        '₦1,234.56'
        >>> format_currency(1234.56, symbol="$")
        '$1,234.56'
        >>> format_currency(1234.56, include_symbol=False)
        '1,234.56'
    """
    formatted = comma_separation(amount)
    if include_symbol:
        return f"{symbol}{formatted}"
    return formatted
