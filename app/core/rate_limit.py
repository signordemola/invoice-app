"""Rate limiting configuration using SlowAPI."""

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings


def get_user_identifier(request: Request) -> str:
    """Get identifier for rate limiting."""

    client_ip = get_remote_address(request)

    user = getattr(request.state, 'user', None)
    if user:
        return f"user:{user.id}"

    return client_ip


def is_ip_exempt(ip: str) -> bool:
    """Check if an IP address is exempt from rate limiting."""
    if not settings.RATE_LIMIT_EXEMPT_IPS:
        return False

    exempt_ips = [
        ip.strip()
        for ip in settings.RATE_LIMIT_EXEMPT_IPS.split(",")
        if ip.strip()
    ]
    return ip in exempt_ips


limiter = Limiter(
    key_func=get_user_identifier,
    default_limits=["100/minute"]
)
