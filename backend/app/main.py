from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.rate_limit import (
    GlobalRateLimitMiddleware,
    limiter,
    rate_limit_exceeded_handler,
)

# Safe to send in every environment.
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "Cross-Origin-Opener-Policy": "same-origin",
}

# Only meaningful over https, so only sent when deployed as production.
HSTS_HEADERS = {
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach browser security headers to every response.

    ``setdefault`` keeps a route's own value: the document download endpoint
    already sets ``Content-Disposition`` and ``Cache-Control``, and those must
    not be overwritten here.
    """

    def __init__(self, app: ASGIApp, headers: dict[str, str]) -> None:
        super().__init__(app)
        self._headers = headers

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)
        for key, value in self._headers.items():
            response.headers.setdefault(key, value)
        return response


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    production = settings.environment == "production"

    # The interactive docs and the OpenAPI document describe every route and
    # payload, which is a map for an attacker. They are decided at construction
    # because FastAPI registers those routes during __init__: clearing the
    # attributes afterwards would leave them serving.
    app = FastAPI(
        title=settings.app_name,
        docs_url=None if production else "/docs",
        redoc_url=None if production else "/redoc",
        openapi_url=None if production else "/openapi.json",
    )
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    # Starlette applies the last-added middleware outermost: CORS wraps the
    # limiter so 429 responses carry CORS headers and OPTIONS preflights are
    # answered before they consume the request budget. Security headers wrap
    # both, so throttled responses and preflights carry them too.
    app.add_middleware(GlobalRateLimitMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    headers = dict(SECURITY_HEADERS)
    if production:
        headers.update(HSTS_HEADERS)
    app.add_middleware(SecurityHeadersMiddleware, headers=headers)
    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()
