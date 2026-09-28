from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_session
from app.core.limiter import get_real_ip, limiter
from app.db.models import EarlyAccessSubscriber
from app.models.early_access import EarlyAccessRequest, EarlyAccessResponse
from app.services.email_service import send_early_access_confirmation_email

router = APIRouter(tags=["early-access"])


@router.post("/early-access", response_model=EarlyAccessResponse, status_code=status.HTTP_200_OK)
@router.post("/waitlist", response_model=EarlyAccessResponse, status_code=status.HTTP_200_OK)
@limiter.limit("5/minute", key_func=get_real_ip)
async def join_early_access(
    payload: EarlyAccessRequest,
    request: Request,
    db: AsyncSession = Depends(get_session),
) -> EarlyAccessResponse:
    """
    Subscribe an email address to early access / waitlist from the landing page.
    Idempotent: if the email is already registered, returns a success confirmation.
    """
    clean_email = payload.email.lower().strip()

    # Check if already subscribed
    result = await db.execute(
        select(EarlyAccessSubscriber).where(EarlyAccessSubscriber.email == clean_email)
    )
    existing = result.scalar_one_or_none()

    if existing:
        return EarlyAccessResponse(
            success=True,
            message="You're already on the list! We'll notify you as soon as there's something to try.",
            email=clean_email,
        )

    # Record new subscriber
    subscriber = EarlyAccessSubscriber(
        email=clean_email,
        source=payload.source,
        ip_address=get_real_ip(request),
    )
    db.add(subscriber)
    await db.commit()

    # Send confirmation email asynchronously / best-effort
    await send_early_access_confirmation_email(clean_email)

    return EarlyAccessResponse(
        success=True,
        message="You're on the list! We'll let you know when there's something to try.",
        email=clean_email,
    )
