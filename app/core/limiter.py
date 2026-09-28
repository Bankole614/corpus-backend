import jwt
from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded

from app.core.config import settings


def get_real_ip(request: Request) -> str:
    """
    Extract the real client IP address, properly inspecting proxy headers
    (X-Forwarded-For, X-Real-IP) before falling back to request.client.host.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # First IP in the comma-separated list is the original client IP
        return forwarded.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    if request.client and request.client.host:
        return request.client.host

    return "127.0.0.1"


def get_client_identifier(request: Request) -> str:
    """
    Returns an authenticated user identifier if a valid Bearer JWT token is present;
    otherwise falls back to the client's real IP address.
    
    This ensures authenticated users behind shared IPs (e.g., offices, universities, NATs)
    are not throttled by each other's traffic on protected endpoints.
    """
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1].strip()
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
                options={"verify_signature": True, "verify_exp": False},
            )
            sub = payload.get("sub")
            if sub:
                return f"usr:{sub}"
        except Exception:
            pass

    return f"ip:{get_real_ip(request)}"


limiter = Limiter(
    key_func=get_client_identifier,
    default_limits=[settings.rate_limit_default] if settings.rate_limit_default else None,
    storage_uri=settings.rate_limit_storage_url,
    enabled=settings.rate_limit_enabled,
    headers_enabled=False,
)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Standardized HTTP 429 response containing both 'detail' (FastAPI standard)
    and 'error' (slowapi standard).
    """
    return JSONResponse(
        status_code=429,
        content={
            "detail": f"Rate limit exceeded: {exc.detail}. Please slow down.",
            "error": f"Rate limit exceeded: {exc.detail}",
        },
    )
