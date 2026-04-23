from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class JobResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., alias="_id", description="Job document ID")
    title: str
    company: str
    location: str
    description: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    employment_type: Optional[str] = None
    source: str
    posted_date: Optional[datetime] = None
    url: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class JobsListResponse(BaseModel):
    items: list[JobResponse]
    page: int
    limit: int
    total: int
    total_pages: int


class SaveJobResponse(BaseModel):
    message: str
    job_id: str


class IngestionResponse(BaseModel):
    source: str
    fetched: int
    inserted: int


class ManualIngestionSummaryResponse(BaseModel):
    usajobs: IngestionResponse
    rss: IngestionResponse
    serpapi: IngestionResponse
    total_inserted: int


class TotalJobsResponse(BaseModel):
    total_jobs: int


class SourceCountResponse(BaseModel):
    source: str
    count: int


class LocationCountResponse(BaseModel):
    location: str
    count: int


class CompanyCountResponse(BaseModel):
    company: str
    count: int
