import hashlib
import ipaddress

from fastapi import Request
from fastapi.responses import JSONResponse, Response
from slowapi import Limiter
from slowapi.middleware import sync_check_limits
from slowapi.util import get_remote_address
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.config import get_settings

settings = get_settings()

DEV_SIGNIN_LIMIT = settings.rate_limit_dev_signin
PASSKEY_BEGIN_LIMIT = settings.rate_limit_passkey_begin
PASSKEY_FINISH_LIMIT = settings.rate_limit_passkey_finish
UPLOAD_LIMIT = settings.rate_limit_upload
DOCUMENT_CONTENT_LIMIT = settings.rate_limit_document_content
EXPORT_LIMIT = settings.rate_limit_export

# Liveness/readiness probes must never consume the global budget: a 10-second
# probe interval would exhaust 200 requests/hour on its own.
EXEMPT_PATHS = frozenset({f"{settings.api_v1_prefix}/health"})


def client_ip(request: Request) -> str:
    """Rate-limit key for anonymous requests.

    X-Forwarded-For is only trusted when explicitly enabled, because any
    client can send that header when the app is exposed directly.
    """
    if settings.trust_proxy_headers:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            candidate = forwarded.split(",", 1)[0].strip()
            try:
                return str(ipaddress.ip_address(candidate))
            except ValueError:
                pass
    return get_remote_address(request)


def _session_key(token: str) -> str:
    # Bearer tokens must never appear in logs. slowapi logs the limit key on
    # a 429, so key on an irreversible digest (the token itself is high
    # entropy, so a plain SHA-256 is enough).
    return f"session:{hashlib.sha256(token.encode('utf-8')).hexdigest()}"


def session_or_ip(request: Request) -> str:
    token = request.cookies.get(settings.cookie_name)
    return _session_key(token) if token else client_ip(request)


limiter = Limiter(
    key_func=client_ip,
    application_limits=[settings.rate_limit_default],
    headers_enabled=True,
    storage_uri=settings.rate_limit_storage_uri,
)

# A second, smaller budget keyed on the session. The IP ceiling alone let one
# citizen exhaust the allowance that everyone behind the same address needs,
# so the per-citizen cap is what actually bounds a single account.
session_limiter = Limiter(
    key_func=session_or_ip,
    application_limits=[settings.rate_limit_session],
    headers_enabled=True,
    storage_uri=settings.rate_limit_storage_uri,
)


def rate_limit_exceeded_handler(request: Request, exc: Exception) -> Response:
    response = JSONResponse(
        status_code=429,
        content={"detail": "Too many requests; please wait before retrying"},
        headers={"Cache-Control": "no-store"},
    )
    current_limit = getattr(request.state, "view_rate_limit", None)
    if current_limit is not None:
        response = request.app.state.limiter._inject_headers(
            response, current_limit
        )
    return response


class GlobalRateLimitMiddleware(BaseHTTPMiddleware):
    """Apply the global per-IP budget to every request, including routes that
    carry their own per-route decorator (slowapi's stock middleware skips
    decorated routes, which would leave them outside the global budget), and
    the per-session budget to requests that carry a session cookie.
    The endpoint is not resolved here: with an empty default-limit set the
    middleware-mode check evaluates only the global application limits, so
    no route lookup is needed (FastAPI's lazy router wrappers expose no
    `endpoint` attribute anyway)."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        app: Starlette = request.app
        if not limiter.enabled or request.url.path in EXEMPT_PATHS:
            return await call_next(request)
        error_response, should_inject_headers = sync_check_limits(
            limiter, request, None, app
        )
        if error_response is not None:
            return error_response
        # Captured before the session budget runs, so the response headers
        # keep describing the ceiling that applied to this request either way.
        ip_limit = request.state.view_rate_limit
        if request.cookies.get(settings.cookie_name):
            session_error, _ = sync_check_limits(
                session_limiter, request, None, app
            )
            if session_error is not None:
                return session_error
        response = await call_next(request)
        if should_inject_headers:
            response = limiter._inject_headers(response, ip_limit)
        return response
