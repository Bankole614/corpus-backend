from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_session
from app.core.deps import get_current_user
from app.core.security import (
    create_access_token,
    create_password_reset_token,
    decode_password_reset_token,
    get_password_fingerprint,
    hash_password,
    verify_google_token,
    verify_password,
)
from app.db.models import User
from app.models.auth import (
    ForgotPasswordRequest,
    GoogleAuthRequest,
    MessageResponse,
    ResetPasswordRequest,
    TokenResponse,
    UserLoginRequest,
    UserOut,
    UserRegisterRequest,
)
from app.services.email_service import send_password_reset_email

router = APIRouter(prefix="/auth", tags=["auth"])


def _user_to_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        avatar_url=user.avatar_url,
        is_admin=user.is_admin,
        created_at=user.created_at,
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: UserRegisterRequest,
    db: AsyncSession = Depends(get_session),
) -> TokenResponse:
    """
    Register a new user with email and password.
    Returns access token and user profile.
    """
    email = request.email.lower().strip()
    result = await db.execute(select(User).where(User.email == email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists",
        )

    # Check if this is the first user in the system to auto-grant admin for local setup
    users_count_result = await db.execute(select(User))
    is_first_user = len(users_count_result.scalars().all()) == 0

    user = User(
        email=email,
        hashed_password=hash_password(request.password),
        full_name=request.full_name,
        is_admin=is_first_user,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token({"sub": user.id})
    return TokenResponse(access_token=token, token_type="bearer", user=_user_to_out(user))


@router.post("/login", response_model=TokenResponse)
async def login(
    request: UserLoginRequest,
    db: AsyncSession = Depends(get_session),
) -> TokenResponse:
    """
    Authenticate with email and password.
    Returns access token and user profile.
    """
    email = request.email.lower().strip()
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is None or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    token = create_access_token({"sub": user.id})
    return TokenResponse(access_token=token, token_type="bearer", user=_user_to_out(user))


@router.post("/google", response_model=TokenResponse)
async def google_auth(
    request: GoogleAuthRequest,
    db: AsyncSession = Depends(get_session),
) -> TokenResponse:
    """
    Authenticate or register using a Google ID token (credential).
    Links with existing account if the email matches.
    """
    try:
        id_info = verify_google_token(request.credential)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    google_id = id_info.get("sub")
    email = id_info.get("email")
    if not email or not google_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google token missing required claims (email, sub)",
        )

    email = email.lower().strip()
    name = id_info.get("name")
    picture = id_info.get("picture")

    # Look up by google_id or email
    result = await db.execute(
        select(User).where((User.google_id == google_id) | (User.email == email))
    )
    user = result.scalars().first()

    if user:
        # Link google_id if not present
        if not user.google_id:
            user.google_id = google_id
        if not user.avatar_url and picture:
            user.avatar_url = picture
        if not user.full_name and name:
            user.full_name = name
        await db.commit()
        await db.refresh(user)
    else:
        # Check if first user
        users_count_result = await db.execute(select(User))
        is_first_user = len(users_count_result.scalars().all()) == 0

        user = User(
            email=email,
            google_id=google_id,
            full_name=name,
            avatar_url=picture,
            is_admin=is_first_user,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    token = create_access_token({"sub": user.id})
    return TokenResponse(access_token=token, token_type="bearer", user=_user_to_out(user))


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)) -> UserOut:
    """
    Get current authenticated user profile.
    """
    return _user_to_out(current_user)


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_session),
) -> MessageResponse:
    """
    Request a password reset link. Always returns a generic success message
    to prevent user enumeration.
    """
    email = request.email.lower().strip()
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    dev_url = None
    if user and user.is_active:
        token = create_password_reset_token(user.id, user.hashed_password)
        reset_url = f"{settings.frontend_url}/reset-password?token={token}"
        await send_password_reset_email(to_email=user.email, reset_url=reset_url, full_name=user.full_name)
        if settings.environment == "development":
            dev_url = reset_url

    return MessageResponse(
        message="If this email is registered, a password reset link has been sent.",
        dev_reset_url=dev_url,
    )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_session),
) -> MessageResponse:
    """
    Reset password using a valid, non-expired password reset token.
    Once used, the token is permanently invalidated.
    """
    payload = decode_password_reset_token(request.token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    user_id = payload.get("sub")
    token_fp = payload.get("fp")
    if not user_id or not token_fp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found or inactive",
        )

    current_fp = get_password_fingerprint(user.hashed_password)
    if current_fp != token_fp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This reset token has already been used or is no longer valid",
        )

    user.hashed_password = hash_password(request.new_password)
    await db.commit()

    return MessageResponse(message="Password has been successfully updated.")
