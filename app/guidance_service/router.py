"""API router for the independent Guidance Service."""

import logging

from fastapi import APIRouter, HTTPException, status

from app.database import get_database
from app.guidance_service import analyze_user_job_guidance
from app.guidance_service.schemas import GuidanceAnalyzeRequest, GuidanceAnalyzeResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/analyze",
    response_model=GuidanceAnalyzeResponse,
    summary="Analyze resume-job skill gap",
    description=(
        "Analyzes the skill gap between a user's stored resume profile and selected job, "
        "then returns categorized missing skills, an algorithmic learning roadmap, "
        "and a preparation strategy."
    ),
)
async def analyze_guidance(payload: GuidanceAnalyzeRequest) -> GuidanceAnalyzeResponse:
    db = get_database()

    try:
        report = await analyze_user_job_guidance(
            db=db,
            user_id=payload.user_id,
            job_id=payload.job_id,
        )
        return GuidanceAnalyzeResponse(**report)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Guidance analysis failed user_id=%s job_id=%s error=%s", payload.user_id, payload.job_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Guidance analysis failed unexpectedly.",
        )
