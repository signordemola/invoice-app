"""Lightweight CSRF middleware using the double-submit cookie pattern."""

from __future__ import annotations

import secrets
from collections.abc import Iterable

from fastapi import Request
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware


SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}


class CSRFMiddleware(BaseHTTPMiddleware):
    """Protect unsafe requests by requiring a matching CSRF cookie and header."""

    def __init__(
        self,
        app,
        cookie_name: str,
        header_name: str,
        secure: bool,
        samesite: str,
        exempt_paths: Iterable[str] | None = None,
    ) -> None:
        super().__init__(app)
        self.cookie_name = cookie_name
        self.header_name = header_name
        self.secure = secure
        self.samesite = samesite
        self.exempt_paths = set(exempt_paths or [])

    async def dispatch(self, request: Request, call_next) -> Response:
        csrf_token = request.cookies.get(self.cookie_name)
        should_seed_cookie = not csrf_token

        if request.method not in SAFE_METHODS and request.url.path not in self.exempt_paths:
            header_token = request.headers.get(self.header_name)
            if (
                not csrf_token
                or not header_token
                or not secrets.compare_digest(csrf_token, header_token)
            ):
                return JSONResponse(
                    status_code=403,
                    content={
                        "error": {
                            "code": "CSRF_VALIDATION_ERROR",
                            "message": "CSRF validation failed",
                            "details": [],
                        }
                    },
                )

        response = await call_next(request)

        if should_seed_cookie:
            response.set_cookie(
                key=self.cookie_name,
                value=secrets.token_urlsafe(32),
                httponly=False,
                secure=self.secure,
                samesite=self.samesite,
                path="/",
            )

        return response
