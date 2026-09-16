from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_session
from app.core.security import decode_access_token
from app.db.models import User

# HTTPBearer scheme for JWT extraction
bearer_scheme = HTTPBearer(auto_error=False)


async def get_optional_current_user(
    auth: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_session),
) -> User | None:
    """
    Returns the authenticated User if a valid Bearer token is provided,
    otherwise returns None. Never raises 401.
    """
    if auth is None or not auth.credentials:
        return None

    payload = decode_access_token(auth.credentials)
    if payload is None:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        return None

    return user


async def get_current_user(
    user: User | None = Depends(get_optional_current_user),
) -> User:
    """
    Requires an authenticated, active User. Raises 401 if missing or invalid.
    """
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_admin_user(
    user: User | None = Depends(get_optional_current_user),
    x_admin_key: str | None = Header(default=None, alias="X-Admin-Key"),
    db: AsyncSession = Depends(get_session),
) -> User:
    """
    Requires either:
    1. Valid X-Admin-Key header matching settings.admin_api_key, OR
    2. Authenticated user with is_admin=True.
    """
    # Check admin API key header first
    if settings.admin_api_key and x_admin_key and x_admin_key == settings.admin_api_key:
        # Check if an admin user exists or return a transient admin user
        result = await db.execute(select(User).where(User.is_admin == True))  # noqa: E712
        admin_user = result.scalars().first()
        if admin_user:
            return admin_user
        # Fallback system admin record
        return User(id="admin-api-key", email="admin@system.local", is_admin=True)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )

    return user
