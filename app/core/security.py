import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any
import bcrypt
import jwt
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from app.core.config import settings


def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt (truncated to 72 bytes per bcrypt limit)."""
    pw_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pw_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its bcrypt hash."""
    if not hashed_password:
        return False
    pw_bytes = plain_password.encode("utf-8")[:72]
    return bcrypt.checkpw(pw_bytes, hashed_password.encode("utf-8"))


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create a signed JWT access token."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({"iat": int(now.timestamp()), "exp": int(expire.timestamp())})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"verify_exp": True},
        )
        return payload
    except Exception:
        return None


def get_password_fingerprint(hashed_password: str | None) -> str:
    """Generate a stable fingerprint of the current password hash for single-use token invalidation."""
    raw = hashed_password or "no-password-set"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def create_password_reset_token(user_id: str, hashed_password: str | None) -> str:
    """Create a short-lived, self-invalidating password reset token."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.password_reset_token_expire_minutes)
    payload = {
        "sub": user_id,
        "purpose": "password_reset",
        "fp": get_password_fingerprint(hashed_password),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_password_reset_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a password reset token."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"verify_exp": True},
        )
        if payload.get("purpose") != "password_reset":
            return None
        return payload
    except Exception:
        return None


def verify_google_token(credential: str) -> dict[str, Any]:
    """
    Verify a Google ID token (credential) from Google Sign-In.
    Returns the token's payload dictionary if valid, or raises ValueError.
    """
    audience = settings.google_client_id if settings.google_client_id else None
    request = google_requests.Request()
    try:
        id_info = google_id_token.verify_oauth2_token(credential, request, audience=audience)
        return id_info
    except Exception as e:
        raise ValueError(f"Invalid Google ID token: {e}") from e
