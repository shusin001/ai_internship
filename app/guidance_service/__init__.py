"""Independent Guidance Service plugin.

This module analyzes skill gaps between a user's resume profile and a selected job,
and returns a structured roadmap and preparation strategy.
"""

import logging
from typing import Any, Dict

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.guidance_service.gap_analyzer import analyze_skill_gap
from app.guidance_service.llm_refiner import maybe_refine_with_gemini
from app.guidance_service.models import build_guidance_report_document
from app.guidance_service.resource_links import generate_resource_links
from app.guidance_service.roadmap_generator import generate_learning_roadmap
from app.guidance_service.skill_extractor import extract_job_skills
from app.guidance_service.strategy_builder import build_preparation_strategy
from app.guidance_service.utils import (
    categorize_missing_skills,
    extract_skills_from_text,
    get_shared_skill_dictionary,
    normalize_skills,
)
from app.resume_service.similarity_engine import compute_cosine_similarity_scores

logger = logging.getLogger(__name__)


def _get_cached_job_skills(resume_profile: Dict[str, Any], job_id: str) -> list[str]:
    recommendation_cache = resume_profile.get("recommendation_cache") or []
    if not isinstance(recommendation_cache, list):
        return []

    for item in recommendation_cache:
        if not isinstance(item, dict):
            continue
        if str(item.get("job_id") or "") != job_id:
            continue
        job_skills = item.get("job_skills") or []
        if isinstance(job_skills, list):
            return normalize_skills(job_skills)
    return []


async def analyze_user_job_guidance(db: AsyncIOMotorDatabase, user_id: str, job_id: str) -> Dict[str, Any]:
    """Run complete guidance analysis for one user-job pair.

    Steps:
    1) Fetch resume profile by `user_id`
    2) Fetch job document by `job_id`
    3) Extract job skills and compute gap
    4) Categorize missing skills
    5) Generate roadmap and strategy
    6) Optionally persist a report in `guidance_reports`
    """
    resume_profile = await db.resume_profiles.find_one({"user_id": user_id})
    if resume_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume profile not found for user.")

    try:
        job_object_id = ObjectId(job_id)
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    job = await db.jobs.find_one({"_id": job_object_id})
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    resume_skills_raw = resume_profile.get("extracted_skills") or []
    if not isinstance(resume_skills_raw, list):
        resume_skills_raw = []

    resume_raw_text = str(resume_profile.get("raw_text") or "")
    dictionary = get_shared_skill_dictionary()
    resume_text_detected_skills = extract_skills_from_text(resume_raw_text, dictionary) if resume_raw_text else []
    resume_skills = normalize_skills(resume_skills_raw + resume_text_detected_skills)

    job_skills = extract_job_skills(job)
    if not job_skills:
        job_skills = _get_cached_job_skills(resume_profile=resume_profile, job_id=job_id)

    if not job_skills:
        empty_categories = {
            "programming_languages": [],
            "frameworks": [],
            "tools": [],
            "cloud": [],
            "databases": [],
            "devops": [],
            "soft_skills": [],
        }
        empty_roadmap = {
            "phase_1": [],
            "phase_2": [],
            "phase_3": [],
            "phase_4": [],
            "phase_5": [],
        }
        strategy = build_preparation_strategy(0.0, empty_categories)
        response = {
            "job_title": str(job.get("title") or "Unknown Job"),
            "current_match_score": 0.0,
            "gap_analysis": {
                "total_job_skills": 0,
                "matched_skills": 0,
                "missing_skills": [],
                "gap_percentage": 0.0,
            },
            "categorized_missing_skills": empty_categories,
            "learning_roadmap": empty_roadmap,
            "preparation_strategy": strategy,
            "resource_links": [],
            "llm_refined": False,
            "llm_daily_remaining": 0,
            "llm_summary": None,
            "llm_status": "Skipped because no job skills were detected.",
            "message": "No detectable skills found in the selected job description.",
        }
        return response

    job_text = "\n".join(
        [
            str(job.get("title") or ""),
            str(job.get("company") or ""),
            str(job.get("location") or ""),
            str(job.get("description") or ""),
        ]
    )
    semantic_similarity = 0.0
    try:
        semantic_scores = compute_cosine_similarity_scores(
            resume_text=resume_raw_text,
            job_texts=[job_text],
        )
        semantic_similarity = float(semantic_scores[0]) if semantic_scores else 0.0
    except Exception as exc:  # pragma: no cover - semantic scoring is best effort
        logger.warning("Semantic similarity scoring failed for user_id=%s job_id=%s error=%s", user_id, job_id, exc)

    gap_result = analyze_skill_gap(
        resume_skills=resume_skills,
        job_skills=job_skills,
        semantic_similarity=semantic_similarity,
    )
    missing_skills = gap_result["missing_skills"]

    categorized = categorize_missing_skills(missing_skills)
    roadmap = generate_learning_roadmap(missing_skills)
    strategy = build_preparation_strategy(gap_result["gap_percentage"], categorized)
    resource_links = generate_resource_links(missing_skills)

    llm_refined, llm_summary, llm_status, llm_daily_remaining = await maybe_refine_with_gemini(
        db=db,
        user_id=user_id,
        report_payload={
            "job_title": str(job.get("title") or "Unknown Job"),
            "gap_analysis": {
                "total_job_skills": gap_result["total_job_skills"],
                "matched_skills": gap_result["matched_skills"],
                "missing_skills": missing_skills,
                "gap_percentage": gap_result["gap_percentage"],
            },
            "learning_roadmap": roadmap,
            "preparation_strategy": strategy,
            "resource_links": resource_links,
        },
    )

    report_payload = {
        "job_title": str(job.get("title") or "Unknown Job"),
        "current_match_score": gap_result["current_match_score"],
        "gap_analysis": {
            "total_job_skills": gap_result["total_job_skills"],
            "matched_skills": gap_result["matched_skills"],
            "missing_skills": missing_skills,
            "gap_percentage": gap_result["gap_percentage"],
        },
        "categorized_missing_skills": categorized,
        "learning_roadmap": roadmap,
        "preparation_strategy": strategy,
        "resource_links": resource_links,
        "llm_refined": llm_refined,
        "llm_daily_remaining": llm_daily_remaining,
        "llm_summary": llm_summary,
        "llm_status": llm_status,
        "message": None,
    }

    if not resume_skills:
        report_payload["message"] = (
            "No explicit resume skills were detected. Guidance used resume text + job requirements."
        )

    guidance_doc = build_guidance_report_document(
        user_id=user_id,
        job_id=job_id,
        missing_skills=missing_skills,
        gap_percentage=gap_result["gap_percentage"],
        roadmap=roadmap,
        strategy=strategy,
        resource_links=resource_links,
        llm_refined=llm_refined,
        llm_summary=llm_summary,
        llm_daily_remaining=llm_daily_remaining,
    )
    try:
        await db.guidance_reports.insert_one(guidance_doc)
    except Exception as exc:  # pragma: no cover - optional persistence should not block response
        logger.error("Failed to persist guidance report user_id=%s job_id=%s error=%s", user_id, job_id, exc)

    return report_payload


from app.guidance_service.router import router  # noqa: E402
