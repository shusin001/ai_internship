from fastapi import APIRouter

from app.database import get_database
from app.schemas.job_schema import (
    CompanyCountResponse,
    LocationCountResponse,
    SourceCountResponse,
    TotalJobsResponse,
)
from app.services.job_service import JobService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get(
    "/total-jobs",
    response_model=TotalJobsResponse,
    summary="Total jobs count",
    description="Returns the total number of job records available in the database.",
)
async def total_jobs() -> TotalJobsResponse:
    service = JobService(get_database())
    return TotalJobsResponse(**(await service.get_total_jobs()))


@router.get(
    "/jobs-by-source",
    response_model=list[SourceCountResponse],
    summary="Jobs grouped by source",
    description="Returns counts split by data source (usajobs/rss).",
)
async def jobs_by_source() -> list[SourceCountResponse]:
    service = JobService(get_database())
    return [SourceCountResponse(**row) for row in await service.get_jobs_by_source()]


@router.get(
    "/top-locations",
    response_model=list[LocationCountResponse],
    summary="Top job locations",
    description="Returns the most frequent job locations in descending order.",
)
async def top_locations() -> list[LocationCountResponse]:
    service = JobService(get_database())
    return [LocationCountResponse(**row) for row in await service.get_top_locations()]


@router.get(
    "/top-companies",
    response_model=list[CompanyCountResponse],
    summary="Top hiring companies",
    description="Returns the most frequent companies in descending order.",
)
async def top_companies() -> list[CompanyCountResponse]:
    service = JobService(get_database())
    return [CompanyCountResponse(**row) for row in await service.get_top_companies()]
