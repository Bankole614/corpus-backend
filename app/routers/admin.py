import json
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.deps import get_admin_user
from app.db.models import (
    Artist,
    ConciergeMessage,
    ConciergeSession,
    TasteProfile,
    User,
    VerificationRecord,
)
from app.models.admin import (
    AdminConciergeSessionItem,
    AdminOverviewMetrics,
    AdminUserDetail,
    AdminUserItem,
    AdminUserUpdate,
    AdminVerificationItem,
)
from app.models.concierge import SessionDetailResponse, SessionMessageOut
from app.models.taste_profile import DescriptiveWord, TasteProfileRequest, TasteProfileResult
from app.services.taste_profile_service import build_summary

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(get_admin_user)])


# ==========================================
# 1. Global Metrics & Platform Stats
# ==========================================
@router.get("/metrics", response_model=AdminOverviewMetrics)
async def get_overview_metrics(db: AsyncSession = Depends(get_session)) -> AdminOverviewMetrics:
    """Fetch global platform statistics across users, verifications, chats, profiles, and artists."""
    total_users_res = await db.execute(select(func.count(User.id)))
    total_users = total_users_res.scalar_one()

    active_users_res = await db.execute(select(func.count(User.id)).where(User.is_active == True))  # noqa: E712
    active_users = active_users_res.scalar_one()

    total_verifications_res = await db.execute(select(func.count(VerificationRecord.id)))
    total_verifications = total_verifications_res.scalar_one()

    total_sessions_res = await db.execute(select(func.count(ConciergeSession.id)))
    total_concierge_sessions = total_sessions_res.scalar_one()

    total_msgs_res = await db.execute(select(func.count(ConciergeMessage.id)))
    total_concierge_messages = total_msgs_res.scalar_one()

    total_profiles_res = await db.execute(select(func.count(TasteProfile.id)))
    total_taste_profiles = total_profiles_res.scalar_one()

    total_artists_res = await db.execute(select(func.count(Artist.id)))
    total_artists = total_artists_res.scalar_one()

    # Verifications grouped by language
    lang_query = select(VerificationRecord.language, func.count(VerificationRecord.id)).group_by(
        VerificationRecord.language
    )
    lang_res = await db.execute(lang_query)
    verifications_by_language = {row[0]: row[1] for row in lang_res.all()}

    return AdminOverviewMetrics(
        total_users=total_users,
        active_users=active_users,
        total_verifications=total_verifications,
        total_concierge_sessions=total_concierge_sessions,
        total_concierge_messages=total_concierge_messages,
        total_taste_profiles=total_taste_profiles,
        total_artists=total_artists,
        verifications_by_language=verifications_by_language,
    )


# ==========================================
# 2. User Management
# ==========================================
@router.get("/users", response_model=list[AdminUserItem])
async def list_users(
    q: str | None = Query(None, description="Search by email or full name"),
    is_admin: bool | None = Query(None, description="Filter by admin status"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_session),
) -> list[AdminUserItem]:
    """List all registered users with their activity metrics."""
    query = select(User)
    if q:
        search_term = f"%{q.strip()}%"
        query = query.where(or_(User.email.ilike(search_term), User.full_name.ilike(search_term)))
    if is_admin is not None:
        query = query.where(User.is_admin == is_admin)
    if is_active is not None:
        query = query.where(User.is_active == is_active)

    query = query.order_by(User.created_at.desc()).offset(offset).limit(limit)
    users = (await db.execute(query)).scalars().all()

    out = []
    for u in users:
        # Count verifications
        v_count_res = await db.execute(
            select(func.count(VerificationRecord.id)).where(VerificationRecord.user_id == u.id)
        )
        v_count = v_count_res.scalar_one()

        # Count sessions
        s_count_res = await db.execute(
            select(func.count(ConciergeSession.id)).where(ConciergeSession.user_id == u.id)
        )
        s_count = s_count_res.scalar_one()

        out.append(
            AdminUserItem(
                id=u.id,
                email=u.email,
                full_name=u.full_name,
                avatar_url=u.avatar_url,
                is_admin=u.is_admin,
                is_active=u.is_active,
                google_id=u.google_id,
                created_at=u.created_at,
                verifications_count=v_count,
                sessions_count=s_count,
            )
        )
    return out


@router.get("/users/{user_id}", response_model=AdminUserDetail)
async def get_user_detail(user_id: str, db: AsyncSession = Depends(get_session)) -> AdminUserDetail:
    """Inspect full user activity (profile, verifications, chats, taste profiles)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    v_count_res = await db.execute(
        select(func.count(VerificationRecord.id)).where(VerificationRecord.user_id == user.id)
    )
    v_count = v_count_res.scalar_one()

    s_count_res = await db.execute(
        select(func.count(ConciergeSession.id)).where(ConciergeSession.user_id == user.id)
    )
    s_count = s_count_res.scalar_one()

    user_item = AdminUserItem(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        avatar_url=user.avatar_url,
        is_admin=user.is_admin,
        is_active=user.is_active,
        google_id=user.google_id,
        created_at=user.created_at,
        verifications_count=v_count,
        sessions_count=s_count,
    )

    # Recent verifications
    v_res = await db.execute(
        select(VerificationRecord)
        .where(VerificationRecord.user_id == user.id)
        .order_by(VerificationRecord.created_at.desc())
        .limit(10)
    )
    recent_verifications = [
        {
            "id": r.id,
            "input_phrase": r.input_phrase,
            "language": r.language,
            "grammatically_valid": r.grammatically_valid,
            "confidence": r.confidence,
            "created_at": r.created_at.isoformat(),
        }
        for r in v_res.scalars().all()
    ]

    # Recent sessions
    s_res = await db.execute(
        select(ConciergeSession)
        .where(ConciergeSession.user_id == user.id)
        .order_by(ConciergeSession.updated_at.desc())
        .limit(10)
    )
    recent_sessions = [
        {
            "session_id": s.id,
            "ready_for_brief": s.ready_for_brief,
            "created_at": s.created_at.isoformat(),
            "updated_at": s.updated_at.isoformat(),
        }
        for s in s_res.scalars().all()
    ]

    # Recent taste profiles
    tp_res = await db.execute(
        select(TasteProfile)
        .where(TasteProfile.user_id == user.id)
        .order_by(TasteProfile.created_at.desc())
        .limit(5)
    )
    recent_taste_profiles = [
        {
            "id": tp.id,
            "descriptive_words": tp.descriptive_words.split(","),
            "line_weight": tp.line_weight,
            "color_approach": tp.color_approach,
            "composition": tp.composition,
            "created_at": tp.created_at.isoformat(),
        }
        for tp in tp_res.scalars().all()
    ]

    return AdminUserDetail(
        user=user_item,
        recent_verifications=recent_verifications,
        recent_sessions=recent_sessions,
        recent_taste_profiles=recent_taste_profiles,
    )


@router.patch("/users/{user_id}", response_model=AdminUserItem)
async def update_user(
    user_id: str,
    update: AdminUserUpdate,
    db: AsyncSession = Depends(get_session),
) -> AdminUserItem:
    """Update user status (ban/activate, change name, grant/revoke admin rights)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if update.is_active is not None:
        user.is_active = update.is_active
    if update.is_admin is not None:
        user.is_admin = update.is_admin
    if update.full_name is not None:
        user.full_name = update.full_name

    await db.commit()
    await db.refresh(user)

    v_count = (
        await db.execute(select(func.count(VerificationRecord.id)).where(VerificationRecord.user_id == user.id))
    ).scalar_one()
    s_count = (
        await db.execute(select(func.count(ConciergeSession.id)).where(ConciergeSession.user_id == user.id))
    ).scalar_one()

    return AdminUserItem(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        avatar_url=user.avatar_url,
        is_admin=user.is_admin,
        is_active=user.is_active,
        google_id=user.google_id,
        created_at=user.created_at,
        verifications_count=v_count,
        sessions_count=s_count,
    )


# ==========================================
# 3. Global Phrase Verifications Oversight
# ==========================================
@router.get("/verifications", response_model=list[AdminVerificationItem])
async def list_all_verifications(
    language: str | None = Query(None, description="Filter by language"),
    valid_only: bool | None = Query(None, description="Filter by grammatically_valid"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_session),
) -> list[AdminVerificationItem]:
    """Global feed of all phrase verifications across all users with user details."""
    query = (
        select(VerificationRecord, User.email)
        .outerjoin(User, VerificationRecord.user_id == User.id)
        .order_by(VerificationRecord.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    if language:
        query = query.where(VerificationRecord.language.ilike(f"%{language}%"))
    if valid_only is not None:
        query = query.where(VerificationRecord.grammatically_valid == valid_only)

    result = await db.execute(query)
    items = []
    for record, user_email in result.all():
        items.append(
            AdminVerificationItem(
                id=record.id,
                user_id=record.user_id,
                user_email=user_email,
                input_phrase=record.input_phrase,
                language=record.language,
                intended_meaning=record.intended_meaning,
                grammatically_valid=record.grammatically_valid,
                confidence=record.confidence,
                corrected_phrase=record.corrected_phrase,
                literal_translation=record.literal_translation,
                recommendation=record.recommendation,
                created_at=record.created_at,
            )
        )
    return items


@router.delete("/verifications/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_any_verification(record_id: str, db: AsyncSession = Depends(get_session)) -> None:
    """Admin endpoint to remove any verification record from history."""
    result = await db.execute(select(VerificationRecord).where(VerificationRecord.id == record_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Verification record not found")
    await db.delete(record)
    await db.commit()


# ==========================================
# 4. Global AI Concierge Oversight
# ==========================================
@router.get("/concierge/sessions", response_model=list[AdminConciergeSessionItem])
async def list_all_concierge_sessions(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_session),
) -> list[AdminConciergeSessionItem]:
    """Global feed of all concierge conversations across the platform."""
    query = (
        select(ConciergeSession, User.email)
        .outerjoin(User, ConciergeSession.user_id == User.id)
        .order_by(ConciergeSession.updated_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(query)
    items = []
    for session, user_email in result.all():
        msg_count = (
            await db.execute(
                select(func.count(ConciergeMessage.id)).where(ConciergeMessage.session_id == session.id)
            )
        ).scalar_one()

        items.append(
            AdminConciergeSessionItem(
                session_id=session.id,
                user_id=session.user_id,
                user_email=user_email,
                ready_for_brief=session.ready_for_brief,
                message_count=msg_count,
                created_at=session.created_at,
                updated_at=session.updated_at,
            )
        )
    return items


@router.get("/concierge/sessions/{session_id}", response_model=SessionDetailResponse)
async def inspect_concierge_session(
    session_id: str, db: AsyncSession = Depends(get_session)
) -> SessionDetailResponse:
    """Admin endpoint to inspect any concierge conversation transcript."""
    result = await db.execute(select(ConciergeSession).where(ConciergeSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    msgs_res = await db.execute(
        select(ConciergeMessage).where(ConciergeMessage.session_id == session_id).order_by(ConciergeMessage.created_at)
    )
    messages = msgs_res.scalars().all()

    return SessionDetailResponse(
        session_id=session.id,
        ready_for_brief=session.ready_for_brief,
        messages=[SessionMessageOut(role=m.role, content=m.content) for m in messages],
    )


@router.delete("/concierge/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_concierge_session(session_id: str, db: AsyncSession = Depends(get_session)) -> None:
    """Admin endpoint to delete any concierge session."""
    result = await db.execute(select(ConciergeSession).where(ConciergeSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    await db.delete(session)
    await db.commit()


# ==========================================
# 5. Global Taste Profiles Oversight
# ==========================================
@router.get("/taste-profiles", response_model=list[TasteProfileResult])
async def list_all_taste_profiles(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_session),
) -> list[TasteProfileResult]:
    """Admin endpoint to view all submitted taste profiles."""
    query = select(TasteProfile).order_by(TasteProfile.created_at.desc()).offset(offset).limit(limit)
    profiles = (await db.execute(query)).scalars().all()

    out = []
    for profile in profiles:
        words = [DescriptiveWord(w) for w in profile.descriptive_words.split(",") if w]
        out.append(
            TasteProfileResult(
                profile_id=profile.id,
                descriptive_words=words,
                line_weight=profile.line_weight,  # type: ignore[arg-type]
                color_approach=profile.color_approach,  # type: ignore[arg-type]
                composition=profile.composition,  # type: ignore[arg-type]
                summary=build_summary(
                    TasteProfileRequest(
                        descriptive_words=words,
                        line_weight=profile.line_weight,  # type: ignore[arg-type]
                        color_approach=profile.color_approach,  # type: ignore[arg-type]
                        composition=profile.composition,  # type: ignore[arg-type]
                    )
                ),
            )
        )
    return out
