from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.database import get_database
from app.routes.users import get_current_user
from app.schemas.job_schema import (
    JobResponse,
    JobsListResponse,
    ManualIngestionSummaryResponse,
    SaveJobResponse,
)
from app.services.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get(
    "",
    response_model=JobsListResponse,
    summary="Search and filter jobs",
    description="Supports keyword text search, filters, pagination, and sorting by posted date.",
)
async def list_jobs(
    keyword: Optional[str] = Query(default=None, description="Text search keyword"),
    location: Optional[str] = Query(default=None, description="Filter by location"),
    employment_type: Optional[str] = Query(default=None, description="Filter by employment type"),
    min_salary: Optional[float] = Query(default=None, ge=0, description="Minimum salary filter"),
    max_salary: Optional[float] = Query(default=None, ge=0, description="Maximum salary filter"),
    page: int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=10, ge=1, le=100, description="Page size"),
) -> JobsListResponse:
    service = JobService(get_database())
    result = await service.list_jobs(
        keyword=keyword,
        location=location,
        employment_type=employment_type,
        min_salary=min_salary,
        max_salary=max_salary,
        page=page,
        limit=limit,
    )
    return JobsListResponse(**result)


@router.get(
    "/{job_id}",
    response_model=JobResponse,
    summary="Get job details",
    description="Returns full details for a single job by ID.",
)
async def get_job_details(job_id: str) -> JobResponse:
    service = JobService(get_database())
    job = await service.get_job_by_id(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
    return JobResponse(**job)


@router.post(
    "/{job_id}/save",
    response_model=SaveJobResponse,
    summary="Save a job for the current user",
    description="Protected endpoint. Adds the given job to the authenticated user's saved jobs.",
)
async def save_job(
    job_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> SaveJobResponse:
    service = JobService(get_database())
    saved = await service.save_job_for_user(current_user["_id"], job_id)
    if not saved:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unable to save job. Job or user may not exist.",
        )
    return SaveJobResponse(message="Job saved successfully.", job_id=job_id)


@router.post(
    "/ingest/manual",
    response_model=ManualIngestionSummaryResponse,
    summary="Manual trigger job ingestion",
    description="Fetches jobs from USAJOBS, RSS, and SerpAPI once, then stores only new jobs.",
)
async def manual_ingestion(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> ManualIngestionSummaryResponse:
    _ = current_user
    service = JobService(get_database())
    result = await service.ingest_all_sources()
    return ManualIngestionSummaryResponse(**result)
