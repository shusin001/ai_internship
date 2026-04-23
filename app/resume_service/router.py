"""Read-only API routes for resume profile and cached recommendations."""

from fastapi import APIRouter, HTTPException, status

from app.database import get_database
from app.resume_service.section_detector import detect_sections
from app.resume_service.skill_extractor import extract_skills
from app.resume_service.recommender import generate_recommendations
from app.resume_service.schemas import (
    ResumeProfileResponseSchema,
    ResumeRecommendationsRefreshResponseSchema,
    ResumeRecommendationsResponseSchema,
)
from app.resume_service.utils import serialize_document

router = APIRouter()


@router.get(
    "/profile/{user_id}",
    response_model=ResumeProfileResponseSchema,
    summary="Get resume profile",
    description="Returns parsed resume profile data from resume_profiles collection.",
)
async def get_resume_profile(user_id: str) -> ResumeProfileResponseSchema:
    db = get_database()
    profile = await db.resume_profiles.find_one({"user_id": user_id})
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume profile not found.")
    return ResumeProfileResponseSchema(**serialize_document(profile))


@router.get(
    "/recommendations/{user_id}",
    response_model=ResumeRecommendationsResponseSchema,
    summary="Get cached recommendations",
    description="Returns recommendation cache from resume_profiles without recomputation.",
)
async def get_cached_recommendations(user_id: str) -> ResumeRecommendationsResponseSchema:
    db = get_database()
    profile = await db.resume_profiles.find_one({"user_id": user_id}, {"recommendation_cache": 1, "user_id": 1})
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume profile not found.")

    recommendations = profile.get("recommendation_cache", [])
    return ResumeRecommendationsResponseSchema(
        user_id=user_id,
        total_recommendations=len(recommendations),
        recommendations=recommendations,
    )


@router.post(
    "/recommendations/{user_id}/refresh",
    response_model=ResumeRecommendationsRefreshResponseSchema,
    summary="Refresh recommendation cache",
    description="Recomputes top recommendations for a user using current ranking logic and updates cache.",
)
async def refresh_recommendations(user_id: str) -> ResumeRecommendationsRefreshResponseSchema:
    db = get_database()
    profile = await db.resume_profiles.find_one({"user_id": user_id}, {"raw_text": 1, "extracted_skills": 1})
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume profile not found.")

    raw_text = str(profile.get("raw_text") or "")
    sections = detect_sections(raw_text)
    refreshed_skills = extract_skills(raw_text, sections) if raw_text else []

    await db.resume_profiles.update_one(
        {"user_id": user_id},
        {"$set": {"extracted_skills": refreshed_skills}},
    )

    recommendations = await generate_recommendations(
        db=db,
        user_id=user_id,
        resume_text=raw_text,
        extracted_skills=refreshed_skills,
        top_k=10,
    )
    return ResumeRecommendationsRefreshResponseSchema(
        user_id=user_id,
        total_recommendations=len(recommendations),
        message="Recommendation cache refreshed successfully.",
    )
