import json
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.db.models import VerificationRecord
from app.models.verification import VerificationRequest, VerificationResult
from app.services.verification_service import VerificationError, verify_phrase

router = APIRouter(prefix="/verify", tags=["verification"])


def _record_to_result(record: VerificationRecord) -> VerificationResult:
    try:
        issues_list = json.loads(record.issues) if record.issues else []
    except Exception:
        issues_list = []

    return VerificationResult(
        id=record.id,
        input_phrase=record.input_phrase,
        language=record.language,
        intended_meaning=record.intended_meaning,
        grammatically_valid=record.grammatically_valid,
        confidence=record.confidence,  # type: ignore[arg-type]
        corrected_phrase=record.corrected_phrase,
        literal_translation=record.literal_translation,
        issues=issues_list,
        historical_usage_notes=record.historical_usage_notes,
        recommendation=record.recommendation,
        created_at=record.created_at,
    )


@router.post("", response_model=VerificationResult)
async def verify(
    request: VerificationRequest,
    db: AsyncSession = Depends(get_session),
) -> VerificationResult:
    """
    Verify any phrase, quote, word, or symbol in any language (Latin, Greek, Sanskrit,
    Japanese, Arabic, French, Spanish, English, etc.) or with auto-detection.
    Returns grammar accuracy, confidence score, corrections, issues, and plain-language
    recommendations, and persists the result to history.
    """
    try:
        result = await verify_phrase(request)
    except VerificationError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    record = VerificationRecord(
        input_phrase=result.input_phrase,
        language=result.language,
        intended_meaning=result.intended_meaning,
        grammatically_valid=result.grammatically_valid,
        confidence=result.confidence,
        corrected_phrase=result.corrected_phrase,
        literal_translation=result.literal_translation,
        issues=json.dumps(result.issues),
        historical_usage_notes=result.historical_usage_notes,
        recommendation=result.recommendation,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    saved_result = _record_to_result(record)
    saved_result.detected_language = result.detected_language
    return saved_result


@router.get("/history", response_model=list[VerificationResult])
async def get_verification_history(
    limit: int = Query(50, ge=1, le=100, description="Maximum number of records to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_session),
) -> list[VerificationResult]:
    """
    Fetch history of phrase verifications, ordered from newest to oldest.
    """
    query = (
        select(VerificationRecord)
        .order_by(VerificationRecord.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(query)
    records = result.scalars().all()
    return [_record_to_result(r) for r in records]


@router.get("/{record_id}", response_model=VerificationResult)
async def get_verification_record(
    record_id: str,
    db: AsyncSession = Depends(get_session),
) -> VerificationResult:
    """
    Retrieve a single verification record by ID.
    """
    result = await db.execute(select(VerificationRecord).where(VerificationRecord.id == record_id))
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=404, detail="Verification record not found")
    return _record_to_result(record)


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_verification_record(
    record_id: str,
    db: AsyncSession = Depends(get_session),
) -> None:
    """
    Delete a single verification record by ID.
    """
    result = await db.execute(select(VerificationRecord).where(VerificationRecord.id == record_id))
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=404, detail="Verification record not found")
    await db.delete(record)
    await db.commit()

