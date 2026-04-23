"""Pydantic schemas for guidance analysis APIs."""

from typing import List, Optional

from pydantic import BaseModel, Field


class GuidanceAnalyzeRequest(BaseModel):
    user_id: str = Field(..., description="User ID from users collection")
    job_id: str = Field(..., description="Job ID from jobs collection")


class GapAnalysisSchema(BaseModel):
    total_job_skills: int
    matched_skills: int
    missing_skills: List[str]
    gap_percentage: float


class CategorizedMissingSkillsSchema(BaseModel):
    programming_languages: List[str]
    frameworks: List[str]
    tools: List[str]
    cloud: List[str]
    databases: List[str]
    devops: List[str]
    soft_skills: List[str]


class LearningRoadmapSchema(BaseModel):
    phase_1: List[str]
    phase_2: List[str]
    phase_3: List[str]
    phase_4: List[str]
    phase_5: List[str]


class PreparationStrategySchema(BaseModel):
    estimated_time: str
    project_suggestions: List[str]
    certification_suggestions: List[str]


class ResourceLinkSchema(BaseModel):
    title: str
    url: str
    platform: str


class GuidanceAnalyzeResponse(BaseModel):
    job_title: str
    current_match_score: float
    gap_analysis: GapAnalysisSchema
    categorized_missing_skills: CategorizedMissingSkillsSchema
    learning_roadmap: LearningRoadmapSchema
    preparation_strategy: PreparationStrategySchema
    resource_links: List[ResourceLinkSchema] = []
    llm_refined: bool = False
    llm_daily_remaining: int = 0
    llm_summary: Optional[str] = None
    llm_status: Optional[str] = None
    message: Optional[str] = None
