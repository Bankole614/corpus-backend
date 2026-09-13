from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.db.models import ConciergeMessage, ConciergeSession
from app.models.concierge import (
    BriefRequest,
    BriefResponse,
    ChatMessage,
    ConciergeChatRequest,
    SendMessageRequest,
    SessionCreateResponse,
    SessionDetailResponse,
    SessionMessageOut,
)
from app.services.concierge_service import ConciergeError, continue_chat, generate_brief

router = APIRouter(prefix="/concierge", tags=["concierge"])


async def _load_session(db: AsyncSession, session_id: str) -> ConciergeSession:
    result = await db.execute(select(ConciergeSession).where(ConciergeSession.id == session_id))
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/sessions", response_model=SessionCreateResponse)
async def create_session(db: AsyncSession = Depends(get_session)) -> SessionCreateResponse:
    session = ConciergeSession()
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return SessionCreateResponse(session_id=session.id)


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session_detail(session_id: str, db: AsyncSession = Depends(get_session)) -> SessionDetailResponse:
    session = await _load_session(db, session_id)
    result = await db.execute(
        select(ConciergeMessage).where(ConciergeMessage.session_id == session_id).order_by(ConciergeMessage.created_at)
    )
    messages = result.scalars().all()
    return SessionDetailResponse(
        session_id=session.id,
        ready_for_brief=session.ready_for_brief,
        messages=[SessionMessageOut(role=m.role, content=m.content) for m in messages],
    )


@router.post("/sessions/{session_id}/messages", response_model=SessionDetailResponse)
async def send_message(
    session_id: str, request: SendMessageRequest, db: AsyncSession = Depends(get_session)
) -> SessionDetailResponse:
    """
    Send a user message in an existing session. Persists it, calls the model with
    the full stored history, persists the assistant's reply, and returns the
    updated session (including the new messages and current ready_for_brief flag).
    """
    session = await _load_session(db, session_id)

    result = await db.execute(
        select(ConciergeMessage).where(ConciergeMessage.session_id == session_id).order_by(ConciergeMessage.created_at)
    )
    existing_messages = result.scalars().all()

    user_msg = ConciergeMessage(session_id=session_id, role="user", content=request.content)
    db.add(user_msg)

    history_for_llm = [ChatMessage(role=m.role, content=m.content) for m in existing_messages]
    history_for_llm.append(ChatMessage(role="user", content=request.content))

    try:
        result_dict = await continue_chat(ConciergeChatRequest(messages=history_for_llm))
    except ConciergeError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    assistant_msg = ConciergeMessage(session_id=session_id, role="assistant", content=result_dict["reply"])
    db.add(assistant_msg)
    session.ready_for_brief = result_dict["ready_for_brief"]

    await db.commit()

    return SessionDetailResponse(
        session_id=session.id,
        ready_for_brief=session.ready_for_brief,
        messages=[
            *[SessionMessageOut(role=m.role, content=m.content) for m in existing_messages],
            SessionMessageOut(role="user", content=request.content),
            SessionMessageOut(role="assistant", content=result_dict["reply"]),
        ],
    )


@router.post("/sessions/{session_id}/brief", response_model=BriefResponse)
async def brief(session_id: str, db: AsyncSession = Depends(get_session)) -> BriefResponse:
    """Generate a structured brief from the session's stored conversation so far."""
    session = await _load_session(db, session_id)
    result = await db.execute(
        select(ConciergeMessage).where(ConciergeMessage.session_id == session_id).order_by(ConciergeMessage.created_at)
    )
    messages = result.scalars().all()
    if not messages:
        raise HTTPException(status_code=400, detail="Session has no messages yet")

    history = [ChatMessage(role=m.role, content=m.content) for m in messages]
    try:
        tattoo_brief = await generate_brief(BriefRequest(messages=history))
    except ConciergeError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    return BriefResponse(brief=tattoo_brief)
