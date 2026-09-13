from fastapi import APIRouter, HTTPException

from app.models.verification import VerificationRequest, VerificationResult
from app.services.verification_service import VerificationError, verify_phrase

router = APIRouter(prefix="/verify", tags=["verification"])


@router.post("", response_model=VerificationResult)
async def verify(request: VerificationRequest) -> VerificationResult:
    """
    Verify a phrase in a supported classical language (Latin, Classical Greek, Sanskrit).
    Returns grammar/accuracy feedback, confidence level, and a plain-language recommendation.
    """
    try:
        return await verify_phrase(request)
    except VerificationError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
