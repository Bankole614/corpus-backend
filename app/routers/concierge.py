import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.deps import get_current_user, get_optional_current_user
from app.db.models import ConciergeMessage, ConciergeSession, User
from app.models.concierge import (
    AttachmentUploadResponse,
    BriefRequest,
    BriefResponse,
    ChatMessage,
    ClearSessionsResponse,
    ConciergeChatRequest,
    SendMessageRequest,
    SessionCreateResponse,
    SessionDeleteResponse,
    SessionDetailResponse,
    SessionMessageOut,
    SessionSummaryOut,
)
from app.services.concierge_service import ConciergeError, continue_chat, generate_brief

router = APIRouter(prefix="/concierge", tags=["concierge"])


async def _load_session(
    db: AsyncSession, session_id: str, current_user: User | None = None
) -> ConciergeSession:
    result = await db.execute(select(ConciergeSession).where(ConciergeSession.id == session_id))
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id is not None:
        if current_user is None or (current_user.id != session.user_id and not current_user.is_admin):
            raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get("/sessions", response_model=list[SessionSummaryOut])
async def list_user_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> list[SessionSummaryOut]:
    """Fetch all concierge chat sessions belonging to the authenticated user."""
    result = await db.execute(
        select(ConciergeSession)
        .where(ConciergeSession.user_id == current_user.id)
        .order_by(ConciergeSession.updated_at.desc())
    )
    sessions = result.scalars().all()
    out = []
    for s in sessions:
        msg_count_res = await db.execute(
            select(func.count(ConciergeMessage.id)).where(ConciergeMessage.session_id == s.id)
        )
        msg_count = msg_count_res.scalar_one()
        out.append(
            SessionSummaryOut(
                session_id=s.id,
                ready_for_brief=s.ready_for_brief,
                created_at=s.created_at,
                updated_at=s.updated_at,
                message_count=msg_count,
            )
        )
    return out


@router.post("/sessions", response_model=SessionCreateResponse)
async def create_session(
    current_user: User | None = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_session),
) -> SessionCreateResponse:
    session = ConciergeSession(user_id=current_user.id if current_user else None)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return SessionCreateResponse(session_id=session.id)


@router.delete("/sessions", response_model=ClearSessionsResponse)
async def clear_all_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> ClearSessionsResponse:
    """
    Deletes all concierge session history and associated messages for the current authenticated user.
    """
    count_res = await db.execute(
        select(func.count(ConciergeSession.id)).where(ConciergeSession.user_id == current_user.id)
    )
    count = count_res.scalar_one()

    if count > 0:
        subquery = select(ConciergeSession.id).where(ConciergeSession.user_id == current_user.id)
        await db.execute(delete(ConciergeMessage).where(ConciergeMessage.session_id.in_(subquery)))
        await db.execute(delete(ConciergeSession).where(ConciergeSession.user_id == current_user.id))
        await db.commit()

    return ClearSessionsResponse(
        message=f"Successfully cleared {count} session(s)" if count > 0 else "No sessions to clear",
        deleted_count=count,
    )


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session_detail(
    session_id: str,
    current_user: User | None = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_session),
) -> SessionDetailResponse:
    session = await _load_session(db, session_id, current_user)
    result = await db.execute(
        select(ConciergeMessage).where(ConciergeMessage.session_id == session_id).order_by(ConciergeMessage.created_at)
    )
    messages = result.scalars().all()
    return SessionDetailResponse(
        session_id=session.id,
        ready_for_brief=session.ready_for_brief,
        messages=[
            SessionMessageOut(role=m.role, content=m.content, image_url=m.image_url)
            for m in messages
        ],
    )


@router.post("/sessions/{session_id}/attachments", response_model=AttachmentUploadResponse)
async def upload_session_attachment(
    session_id: str,
    file: UploadFile = File(...),
    current_user: User | None = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_session),
) -> AttachmentUploadResponse:
    """
    Upload an image reference for a concierge chat session.
    Saves image under /static/concierge/ and returns image_url for inclusion in messages.
    """
    await _load_session(db, session_id, current_user)

    if not file.content_type or not (
        file.content_type.startswith("image/") or file.content_type == "application/octet-stream"
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be a valid image.",
        )

    filename = file.filename or "reference.png"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png", ".webp", ".gif", ".heic"]:
        ext = ".png"

    concierge_dir = "app/static/concierge"
    os.makedirs(concierge_dir, exist_ok=True)
    stored_filename = f"{session_id}_{uuid.uuid4().hex[:8]}{ext}"
    filepath = os.path.join(concierge_dir, stored_filename)

    contents = await file.read()
    if len(contents) > 20 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image size exceeds 20MB limit.",
        )

    with open(filepath, "wb") as f:
        f.write(contents)

    return AttachmentUploadResponse(image_url=f"/static/concierge/{stored_filename}")


@router.delete("/sessions/{session_id}", response_model=SessionDeleteResponse)
async def delete_session(
    session_id: str,
    current_user: User | None = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_session),
) -> SessionDeleteResponse:
    """
    Deletes a specific concierge session and its associated messages.
    Requires ownership of the session (or admin privileges).
    """
    session = await _load_session(db, session_id, current_user)

    await db.execute(delete(ConciergeMessage).where(ConciergeMessage.session_id == session.id))
    await db.delete(session)
    await db.commit()

    return SessionDeleteResponse(
        message="Session deleted successfully",
        session_id=session_id,
    )


@router.post("/sessions/{session_id}/messages", response_model=SessionDetailResponse)
async def send_message(
    session_id: str,
    request: SendMessageRequest,
    current_user: User | None = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_session),
) -> SessionDetailResponse:
    """
    Send a user message in an existing session. Persists it, calls the model with
    the full stored history (including images), persists the assistant's reply, and returns the
    updated session (including the new messages and current ready_for_brief flag).
    """
    session = await _load_session(db, session_id, current_user)

    content = (request.content or "").strip()
    image_url = (request.image_url or "").strip() or None

    if not content and not image_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either message content or an image_url must be provided.",
        )

    if not content and image_url:
        content = "Here is an image reference for my tattoo idea."

    result = await db.execute(
        select(ConciergeMessage).where(ConciergeMessage.session_id == session_id).order_by(ConciergeMessage.created_at)
    )
    existing_messages = result.scalars().all()

    user_msg = ConciergeMessage(
        session_id=session_id,
        role="user",
        content=content,
        image_url=image_url,
    )
    db.add(user_msg)

    history_for_llm = [
        ChatMessage(role=m.role, content=m.content, image_url=m.image_url)
        for m in existing_messages
    ]
    history_for_llm.append(ChatMessage(role="user", content=content, image_url=image_url))

    try:
        result_dict = await continue_chat(ConciergeChatRequest(messages=history_for_llm))
    except ConciergeError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    assistant_msg = ConciergeMessage(
        session_id=session_id,
        role="assistant",
        content=result_dict["reply"],
        image_url=None,
    )
    db.add(assistant_msg)
    session.ready_for_brief = result_dict["ready_for_brief"]

    await db.commit()

    return SessionDetailResponse(
        session_id=session.id,
        ready_for_brief=session.ready_for_brief,
        messages=[
            *[SessionMessageOut(role=m.role, content=m.content, image_url=m.image_url) for m in existing_messages],
            SessionMessageOut(role="user", content=content, image_url=image_url),
            SessionMessageOut(role="assistant", content=result_dict["reply"], image_url=None),
        ],
    )


@router.post("/sessions/{session_id}/brief", response_model=BriefResponse)
async def brief(
    session_id: str,
    current_user: User | None = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_session),
) -> BriefResponse:
    """Generate a structured brief from the session's stored conversation so far."""
    session = await _load_session(db, session_id, current_user)
    result = await db.execute(
        select(ConciergeMessage).where(ConciergeMessage.session_id == session_id).order_by(ConciergeMessage.created_at)
    )
    messages = result.scalars().all()
    if not messages:
        raise HTTPException(status_code=400, detail="Session has no messages yet")

    history = [
        ChatMessage(role=m.role, content=m.content, image_url=m.image_url)
        for m in messages
    ]
    try:
        tattoo_brief = await generate_brief(BriefRequest(messages=history))
    except ConciergeError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    return BriefResponse(brief=tattoo_brief)
