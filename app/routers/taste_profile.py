from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.db.models import TasteProfile
from app.models.taste_profile import DescriptiveWord, TasteProfileRequest, TasteProfileResult
from app.services.taste_profile_service import build_summary

router = APIRouter(prefix="/taste-profile", tags=["taste-profile"])


def _to_result(profile: TasteProfile) -> TasteProfileResult:
    words = [DescriptiveWord(w) for w in profile.descriptive_words.split(",") if w]
    return TasteProfileResult(
        profile_id=profile.id,
        descriptive_words=words,
        line_weight=profile.line_weight,
        color_approach=profile.color_approach,
        composition=profile.composition,
        summary=build_summary(
            TasteProfileRequest(
                descriptive_words=words,
                line_weight=profile.line_weight,
                color_approach=profile.color_approach,
                composition=profile.composition,
            )
        ),
    )


@router.post("", response_model=TasteProfileResult)
async def submit_taste_profile(
    request: TasteProfileRequest, db: AsyncSession = Depends(get_session)
) -> TasteProfileResult:
    profile = TasteProfile(
        descriptive_words=",".join(w.value for w in request.descriptive_words),
        line_weight=request.line_weight,
        color_approach=request.color_approach,
        composition=request.composition,
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return _to_result(profile)


@router.get("/{profile_id}", response_model=TasteProfileResult)
async def get_taste_profile(profile_id: str, db: AsyncSession = Depends(get_session)) -> TasteProfileResult:
    result = await db.execute(select(TasteProfile).where(TasteProfile.id == profile_id))
    profile = result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(status_code=404, detail="Taste profile not found")
    return _to_result(profile)
