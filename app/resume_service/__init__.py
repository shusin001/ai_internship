"""Resume intelligence service plugin.

This module isolates parsing, extraction, and recommendation logic so failures in
resume processing do not impact the core registration path.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.resume_service.experience_estimator import estimate_experience_years
from app.resume_service.models import build_resume_profile_document
from app.resume_service.parser import extract_text_from_pdf
from app.resume_service.recommender import generate_recommendations
from app.resume_service.section_detector import detect_sections
from app.resume_service.skill_extractor import extract_skills
from app.resume_service.utils import sanitize_email, validate_pdf_file

logger = logging.getLogger(__name__)


def _extract_list_items(section_text: Optional[str]) -> List[str]:
    if not section_text:
        return []

    cleaned = section_text.replace("\t", " ")
    parts = []
    for line in cleaned.splitlines():
        stripped = line.strip(" -•*\t").strip()
        if not stripped:
            continue
        for segment in stripped.split(","):
            item = segment.strip()
            if item:
                parts.append(item)

    deduped = []
    seen = set()
    for item in parts:
        key = item.lower()
        if key not in seen:
            deduped.append(item)
            seen.add(key)
    return deduped


async def process_resume(
    db: AsyncIOMotorDatabase,
    user_id: str,
    name: Optional[str],
    email: str,
    filename: Optional[str],
    content_type: Optional[str],
    file_bytes: bytes,
) -> Dict[str, Any]:
    """Process resume and persist structured profile + cached recommendations."""
    validate_pdf_file(filename=filename, content_type=content_type, file_bytes=file_bytes)

    raw_text = await asyncio.to_thread(extract_text_from_pdf, file_bytes)
    extracted_sections = detect_sections(raw_text)
    extracted_skills = await asyncio.to_thread(extract_skills, raw_text, extracted_sections)

    certifications = _extract_list_items(extracted_sections.get("certifications"))
    projects = _extract_list_items(extracted_sections.get("projects"))
    experience_source = extracted_sections.get("experience") or raw_text
    experience_years = estimate_experience_years(experience_source)

    profile_doc = build_resume_profile_document(
        user_id=user_id,
        name=name,
        email=sanitize_email(email),
        raw_text=raw_text,
        extracted_sections=extracted_sections,
        extracted_skills=extracted_skills,
        certifications=certifications,
        projects=projects,
        experience_years_estimated=experience_years,
    )

    created_at = profile_doc.pop("created_at")
    await db.resume_profiles.update_one(
        {"user_id": user_id},
        {
            "$set": profile_doc,
            "$setOnInsert": {"created_at": created_at},
        },
        upsert=True,
    )

    try:
        recommendations = await generate_recommendations(
            db=db,
            user_id=user_id,
            resume_text=raw_text,
            extracted_skills=extracted_skills,
            top_k=10,
        )
    except Exception as exc:
        logger.exception("Recommendation generation failed for user_id=%s error=%s", user_id, exc)
        recommendations = []

    try:
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "resume_uploaded": True,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
    except Exception as exc:
        logger.error("Failed to update resume_uploaded flag for user_id=%s error=%s", user_id, exc)

    return {
        "user_id": user_id,
        "skills_count": len(extracted_skills),
        "recommendation_count": len(recommendations),
    }


async def safe_process_resume(
    db: AsyncIOMotorDatabase,
    user_id: str,
    name: Optional[str],
    email: str,
    filename: Optional[str],
    content_type: Optional[str],
    file_bytes: bytes,
) -> None:
    """Non-throwing wrapper for background resume processing."""
    try:
        await process_resume(
            db=db,
            user_id=user_id,
            name=name,
            email=email,
            filename=filename,
            content_type=content_type,
            file_bytes=file_bytes,
        )
    except Exception as exc:  # pragma: no cover - fail-safe for registration path
        logger.exception("Resume processing failed for user_id=%s error=%s", user_id, exc)


from app.resume_service.router import router  # noqa: E402
