"""Pydantic schemas for scraping/injection service."""

from pydantic import BaseModel, Field


class InjectJobsRequest(BaseModel):
    max_results: int = Field(default=20, ge=5, le=50)
    refresh_recommendations: bool = Field(default=True)


class InjectJobsResponse(BaseModel):
    user_id: str
    query: str
    fetched: int
    inserted: int
    refreshed_recommendations: bool
