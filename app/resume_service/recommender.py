"""Recommendation engine for resume-job matching."""

import logging
import re
from datetime import datetime, timezone
from typing import Dict, List

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.resume_service.similarity_engine import (
    compute_cosine_similarity_scores,
    compute_skill_overlap_scores,
)
from app.resume_service.utils import load_skill_dictionary
from app.utils.helpers import parse_datetime

logger = logging.getLogger(__name__)

TECH_SIGNAL_SKILLS = {
    "python",
    "java",
    "javascript",
    "typescript",
    "react",
    "node.js",
    "fastapi",
    "django",
    "flask",
    "sql",
    "mongodb",
    "mysql",
    "postgresql",
    "docker",
    "kubernetes",
    "aws",
    "azure",
    "gcp",
    "spark",
    "airflow",
    "etl",
    "machine learning",
    "nlp",
    "ai",
    "rest api",
    "github actions",
}

NON_TECH_TITLE_HINTS = {
    "social worker",
    "caregiver",
    "case administrator",
    "budget analyst",
    "recreation specialist",
    "program coordinator",
}


def _normalize_skills(skills: List[str]) -> List[str]:
    return sorted({skill.strip().lower() for skill in skills if isinstance(skill, str) and skill.strip()})


def _extract_detected_skills(text: str, skill_dictionary: List[str]) -> List[str]:
    text_lc = (text or "").lower()
    detected: List[str] = []
    for skill in skill_dictionary:
        if skill == "c":
            if not re.search(r"\b(c language|c programming|ansi c)\b", text_lc):
                continue
        escaped = re.escape(skill)
        if re.search(rf"(?<!\w){escaped}(?!\w)", text_lc):
            detected.append(skill)
    return sorted(set(detected))


def _derive_resume_title_hints(resume_text: str, resume_skills: List[str]) -> List[str]:
    text_lc = (resume_text or "").lower()
    hints = []

    role_hints = [
        "software engineer",
        "software development",
        "full-stack",
        "full stack",
        "backend",
        "frontend",
        "ai",
        "machine learning",
        "data engineer",
        "data scientist",
        "devops",
        "cloud",
        "automation",
        "security",
        "operations",
        "operations specialist",
        "content moderation",
        "content management",
        "customer support",
        "program coordinator",
        "project coordinator",
        "manager",
        "analyst",
        "specialist",
    ]

    for hint in role_hints:
        if hint in text_lc:
            hints.append(hint)

    skill_set = set(resume_skills)
    if len(skill_set.intersection(TECH_SIGNAL_SKILLS)) >= 4:
        hints.extend(["engineer", "developer", "software"])
    elif len(skill_set.intersection({"communication", "leadership", "project management", "problem solving"})) >= 2:
        hints.extend(["specialist", "coordinator", "manager", "operations"])

    return sorted(set(hints))


def _title_role_alignment_score(title: str, resume_title_hints: List[str]) -> float:
    if not resume_title_hints:
        return 0.0
    title_lc = (title or "").lower()
    matched = sum(1 for hint in resume_title_hints if hint in title_lc)
    denominator = float(min(3, len(resume_title_hints)))
    if denominator == 0.0:
        return 0.0
    return max(0.0, min(1.0, matched / denominator))


def _title_skill_focus_score(title: str, resume_skills: List[str]) -> float:
    title_lc = (title or "").lower()
    normalized_skills = [skill.lower() for skill in resume_skills if isinstance(skill, str) and skill.strip()]
    if not normalized_skills:
        return 0.0

    matched = sum(1 for skill in set(normalized_skills) if skill in title_lc)
    return matched / float(len(set(normalized_skills)))


def _recency_score(posted_date_value) -> float:
    parsed = parse_datetime(posted_date_value)
    if parsed is None:
        return 0.0
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    days_old = max(0.0, (datetime.now(timezone.utc) - parsed).total_seconds() / 86400.0)
    # 60-day linear freshness window.
    return max(0.0, min(1.0, 1.0 - (days_old / 60.0)))


def _job_skill_coverage_score(resume_skills: List[str], job_skills: List[str]) -> float:
    resume_set = set(_normalize_skills(resume_skills))
    job_set = set(_normalize_skills(job_skills))
    if not resume_set or not job_set:
        return 0.0
    matched = len(resume_set.intersection(job_set))
    return matched / float(len(job_set))


def _domain_alignment_factor(resume_skills: List[str], job_skills: List[str], job_title: str) -> float:
    resume_tech = len(set(_normalize_skills(resume_skills)).intersection(TECH_SIGNAL_SKILLS))
    if resume_tech < 4:
        return 1.0

    job_skill_set = set(_normalize_skills(job_skills))
    job_tech = len(job_skill_set.intersection(TECH_SIGNAL_SKILLS))
    title_lc = (job_title or "").lower()

    if job_tech >= 2:
        return 1.0
    if job_tech == 1:
        return 0.85
    if any(token in title_lc for token in NON_TECH_TITLE_HINTS):
        return 0.35
    if any(token in title_lc for token in ["engineer", "developer", "software", "systems", "it"]):
        return 0.8
    return 0.45


def _build_match_note(
    cosine: float,
    overlap: float,
    title_focus: float,
    role_focus: float,
    job_coverage: float,
    domain_factor: float,
) -> str:
    """Create concise explanation of why a job was ranked highly.

    Includes both semantic similarity and skill overlap signals.
    """
    semantic_pct = int(round(max(0.0, min(1.0, cosine)) * 100))
    overlap_pct = int(round(max(0.0, min(1.0, overlap)) * 100))
    title_pct = int(round(max(0.0, min(1.0, title_focus)) * 100))
    role_pct = int(round(max(0.0, min(1.0, role_focus)) * 100))
    coverage_pct = int(round(max(0.0, min(1.0, job_coverage)) * 100))
    domain_pct = int(round(max(0.0, min(1.0, domain_factor)) * 100))
    return (
        "Ranked by semantic alignment {}%, skill overlap {}%, title-skill focus {}%, "
        "role-title alignment {}%, and job-skill coverage {}% (domain fit {}%)."
    ).format(semantic_pct, overlap_pct, title_pct, role_pct, coverage_pct, domain_pct)


async def generate_recommendations(
    db: AsyncIOMotorDatabase,
    user_id: str,
    resume_text: str,
    extracted_skills: List[str],
    top_k: int = 10,
) -> List[Dict]:
    """Compute and persist top-N recommendations in resume_profiles.

    final_score = (
        0.55 * cosine_similarity
        + 0.30 * skill_overlap
        + 0.10 * title_skill_focus
        + 0.05 * recency_score
    )
    """
    jobs = await db.jobs.find(
        {},
        {
            "_id": 1,
            "title": 1,
            "description": 1,
            "company": 1,
            "location": 1,
            "posted_date": 1,
        },
    ).to_list(length=10000)

    if not jobs:
        await db.resume_profiles.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "recommendation_cache": [],
                    "updated_at": datetime.now(timezone.utc),
                }
            },
            upsert=True,
        )
        return []

    job_texts = []
    skill_dictionary = load_skill_dictionary()
    normalized_resume_skills = _normalize_skills(extracted_skills)
    resume_title_hints = _derive_resume_title_hints(resume_text=resume_text, resume_skills=normalized_resume_skills)

    for job in jobs:
        title = job.get("title") or ""
        description = job.get("description") or ""
        company = job.get("company") or ""
        location = job.get("location") or ""
        job_texts.append(f"{title}\n{company}\n{location}\n{description}")

    cosine_scores = compute_cosine_similarity_scores(resume_text=resume_text, job_texts=job_texts)
    skill_scores = compute_skill_overlap_scores(resume_skills=normalized_resume_skills, job_texts=job_texts)
    job_detected_skills = [_extract_detected_skills(text, skill_dictionary) for text in job_texts]

    ranked_all = []
    ranked_filtered = []
    for index, job in enumerate(jobs):
        cosine = cosine_scores[index] if index < len(cosine_scores) else 0.0
        overlap = skill_scores[index] if index < len(skill_scores) else 0.0
        title = job.get("title") or ""
        current_job_skills = job_detected_skills[index] if index < len(job_detected_skills) else []
        title_focus = _title_skill_focus_score(title, normalized_resume_skills)
        role_focus = _title_role_alignment_score(title=title, resume_title_hints=resume_title_hints)
        job_coverage = _job_skill_coverage_score(normalized_resume_skills, current_job_skills)
        domain_factor = _domain_alignment_factor(
            resume_skills=normalized_resume_skills,
            job_skills=current_job_skills,
            job_title=title,
        )
        freshness = _recency_score(job.get("posted_date"))

        # Hybrid ranking for stronger alignment:
        # 40% semantic relevance + 25% skill overlap + 15% title-skill focus +
        # 10% job-skill coverage + 5% role-title alignment + 5% recency.
        # Domain alignment factor penalizes jobs that conflict with resume domain.
        final_score = (
            (0.40 * cosine)
            + (0.25 * overlap)
            + (0.15 * title_focus)
            + (0.10 * job_coverage)
            + (0.05 * role_focus)
            + (0.05 * freshness)
        )
        final_score = final_score * domain_factor

        item = {
            "job_id": str(job["_id"]),
            "score": round(float(final_score), 6),
            "job_skills": current_job_skills,
            "match_note": _build_match_note(
                cosine=cosine,
                overlap=overlap,
                title_focus=title_focus,
                role_focus=role_focus,
                job_coverage=job_coverage,
                domain_factor=domain_factor,
            ),
        }
        ranked_all.append(item)

        # Filter clearly weak cross-domain matches to keep top results relevant.
        low_quality_domain_mismatch = (
            domain_factor <= 0.45
            and cosine < 0.08
            and overlap < 0.10
            and role_focus < 0.20
        )
        if not low_quality_domain_mismatch:
            ranked_filtered.append(item)

    ranked_filtered.sort(key=lambda row: row["score"], reverse=True)
    ranked_all.sort(key=lambda row: row["score"], reverse=True)

    # If filtering removed too many results, gracefully fall back to all-ranked items.
    candidate_list = ranked_filtered if len(ranked_filtered) >= min(3, top_k) else ranked_all
    top_results = candidate_list[:top_k]

    await db.resume_profiles.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "recommendation_cache": top_results,
                "updated_at": datetime.now(timezone.utc),
            }
        },
        upsert=True,
    )

    logger.info("Recommendation cache updated for user_id=%s count=%s", user_id, len(top_results))
    return top_results
