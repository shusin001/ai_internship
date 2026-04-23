"""Pydantic schemas for resume service API responses."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ExtractedSectionsSchema(BaseModel):
    skills: Optional[str] = None
    certifications: Optional[str] = None
    experience: Optional[str] = None
    projects: Optional[str] = None
    summary: Optional[str] = None


class RecommendationCacheItemSchema(BaseModel):
    job_id: str
    score: float
    match_note: Optional[str] = None


class ResumeProfileResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., alias="_id")
    user_id: str
    name: Optional[str] = None
    email: EmailStr
    raw_text: str
    extracted_sections: ExtractedSectionsSchema
    extracted_skills: List[str]
    certifications: List[str]
    projects: List[str]
    experience_years_estimated: Optional[float] = None
    recommendation_cache: List[RecommendationCacheItemSchema]
    created_at: datetime
    updated_at: datetime


class ResumeRecommendationsResponseSchema(BaseModel):
    user_id: str
    total_recommendations: int
    recommendations: List[RecommendationCacheItemSchema]


class ResumeRecommendationsRefreshResponseSchema(BaseModel):
    user_id: str
    total_recommendations: int
    message: str
