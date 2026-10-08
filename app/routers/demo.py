import logging
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_session
from app.core.limiter import get_real_ip, limiter
from app.db.models import DemoRequestRecord
from app.models.demo import DemoRequestPayload, DemoResponse
from app.services.email_service import (
    send_demo_request_confirmation_email,
    send_demo_request_notification_to_admin,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["demo"])


@router.post("/request-demo", response_model=DemoResponse, status_code=status.HTTP_200_OK)
@router.post("/demo-request", response_model=DemoResponse, status_code=status.HTTP_200_OK)
@limiter.limit("5/minute", key_func=get_real_ip)
async def request_demo(
    payload: DemoRequestPayload,
    request: Request,
    db: AsyncSession = Depends(get_session),
) -> DemoResponse:
    """
    Submit a demo request from the Corpus landing page.
    Saves the demo request to the database, notifies the owner/admin email,
    and sends a confirmation email to the requester.
    """
    clean_email = payload.email.lower().strip()
    client_ip = get_real_ip(request)

    # Save to database
    record = DemoRequestRecord(
        email=clean_email,
        name=payload.name.strip() if payload.name else None,
        notes=payload.notes.strip() if payload.notes else None,
        source=payload.source,
        ip_address=client_ip,
    )
    db.add(record)
    await db.commit()

    # Best-effort asynchronous emails
    try:
        await send_demo_request_notification_to_admin(
            requester_email=clean_email,
            requester_name=payload.name,
            requester_notes=payload.notes,
            ip_address=client_ip,
        )
    except Exception as e:
        logger.error(f"Failed to notify admin of demo request from {clean_email}: {e}")

    try:
        await send_demo_request_confirmation_email(
            to_email=clean_email,
            requester_name=payload.name,
        )
    except Exception as e:
        logger.error(f"Failed to send confirmation email to {clean_email}: {e}")

    return DemoResponse(
        success=True,
        message="Thank you! We've received your demo request and will reach out shortly.",
        email=clean_email,
    )
