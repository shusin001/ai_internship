"""Routes for independent scraping/injection service."""

import logging

from fastapi import APIRouter, HTTPException, status

from app.database import get_database
from app.scraping_service import inject_preferred_jobs_for_user
from app.scraping_service.schemas import InjectJobsRequest, InjectJobsResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/inject/{user_id}",
    response_model=InjectJobsResponse,
    summary="Scrape and inject preferred jobs",
    description=(
        "Uses SerpAPI to scrape jobs based on resume profile, injects new jobs into the shared jobs collection, "
        "and optionally refreshes recommendation cache."
    ),
)
async def inject_jobs_for_user(user_id: str, payload: InjectJobsRequest) -> InjectJobsResponse:
    db = get_database()

    try:
        result = await inject_preferred_jobs_for_user(
            db=db,
            user_id=user_id,
            max_results=payload.max_results,
            refresh_recommendations=payload.refresh_recommendations,
        )
        return InjectJobsResponse(**result)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Scraping injection failed user_id=%s error=%s", user_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Scraping/injection failed unexpectedly.",
        )
