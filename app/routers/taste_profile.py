from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.deps import get_current_user, get_optional_current_user
from app.db.models import TasteProfile, User, UserSavedTasteStyle
from app.models.taste_profile import (
    DescriptiveWord,
    SaveStyleRequest,
    SavedStyleActionResponse,
    SavedStylesResponse,
    StyleCardItem,
    SyncStyleRequest,
    TasteProfileRequest,
    TasteProfileResult,
)
from app.services.taste_profile_service import build_summary, get_default_style_deck

router = APIRouter(prefix="/taste-profile", tags=["taste-profile"])


def _to_result(profile: TasteProfile) -> TasteProfileResult:
    words = [DescriptiveWord(w) for w in profile.descriptive_words.split(",") if w]
    return TasteProfileResult(
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


@router.get("/deck", response_model=list[StyleCardItem])
async def get_taste_deck(
    limit: int = Query(100, ge=1, le=150, description="Number of style cards to return"),
) -> list[StyleCardItem]:
    """
    Fetch the curated swipe deck of real tattoo photos with style tags
    for the interactive taste discovery quiz.
    """
    return get_default_style_deck(limit=limit)


@router.post("", response_model=TasteProfileResult)
async def submit_taste_profile(
    request: TasteProfileRequest,
    current_user: User | None = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_session),
) -> TasteProfileResult:
    profile = TasteProfile(
        user_id=current_user.id if current_user else None,
        descriptive_words=",".join(w.value for w in request.descriptive_words),
        line_weight=request.line_weight,
        color_approach=request.color_approach,
        composition=request.composition,
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return _to_result(profile)


@router.get("/me", response_model=TasteProfileResult)
async def get_my_taste_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> TasteProfileResult:
    """Fetch the latest taste profile for the authenticated user."""
    result = await db.execute(
        select(TasteProfile)
        .where(TasteProfile.user_id == current_user.id)
        .order_by(TasteProfile.created_at.desc())
    )
    profile = result.scalars().first()
    if profile is None:
        raise HTTPException(status_code=404, detail="No taste profile found for this user")
    return _to_result(profile)


async def _get_user_saved_style_ids(user_id: str, db: AsyncSession) -> list[str]:
    result = await db.execute(
        select(UserSavedTasteStyle.style_id)
        .where(UserSavedTasteStyle.user_id == user_id)
        .order_by(UserSavedTasteStyle.created_at.asc())
    )
    return list(result.scalars().all())


@router.get("/saved", response_model=SavedStylesResponse)
async def get_saved_taste_styles(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> SavedStylesResponse:
    """Fetch all saved taste style IDs for the logged-in user."""
    saved_ids = await _get_user_saved_style_ids(current_user.id, db)
    return SavedStylesResponse(saved_style_ids=saved_ids)


@router.post("/saved", response_model=SavedStylesResponse)
async def save_taste_style_item(
    payload: SaveStyleRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> SavedStylesResponse:
    """Bookmark a style card for the authenticated user."""
    clean_id = payload.style_id.strip()
    result = await db.execute(
        select(UserSavedTasteStyle).where(
            UserSavedTasteStyle.user_id == current_user.id,
            UserSavedTasteStyle.style_id == clean_id,
        )
    )
    existing = result.scalar_one_or_none()

    if not existing:
        new_entry = UserSavedTasteStyle(user_id=current_user.id, style_id=clean_id)
        db.add(new_entry)
        await db.commit()

    saved_ids = await _get_user_saved_style_ids(current_user.id, db)
    return SavedStylesResponse(saved_style_ids=saved_ids)


@router.delete("/saved/{style_id}", response_model=SavedStyleActionResponse)
async def unsave_taste_style_item(
    style_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> SavedStyleActionResponse:
    """Remove a bookmarked style card for the authenticated user."""
    clean_id = style_id.strip()
    await db.execute(
        delete(UserSavedTasteStyle).where(
            UserSavedTasteStyle.user_id == current_user.id,
            UserSavedTasteStyle.style_id == clean_id,
        )
    )
    await db.commit()
    return SavedStyleActionResponse(status="success")


@router.post("/saved/sync", response_model=SavedStylesResponse)
async def sync_saved_taste_styles(
    payload: SyncStyleRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> SavedStylesResponse:
    """Merge local offline bookmarks with user cloud database."""
    current_saved = set(await _get_user_saved_style_ids(current_user.id, db))

    for raw_id in payload.saved_style_ids:
        clean_id = raw_id.strip()
        if clean_id and clean_id not in current_saved:
            db.add(UserSavedTasteStyle(user_id=current_user.id, style_id=clean_id))
            current_saved.add(clean_id)

    await db.commit()
    saved_ids = await _get_user_saved_style_ids(current_user.id, db)
    return SavedStylesResponse(saved_style_ids=saved_ids)


@router.get("/{profile_id}", response_model=TasteProfileResult)
async def get_taste_profile(profile_id: str, db: AsyncSession = Depends(get_session)) -> TasteProfileResult:
    result = await db.execute(select(TasteProfile).where(TasteProfile.id == profile_id))
    profile = result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(status_code=404, detail="Taste profile not found")
    return _to_result(profile)

