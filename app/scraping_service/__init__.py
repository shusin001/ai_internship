"""Independent scraping/injection plugin for external job discovery."""

import logging
from typing import Dict, List, Set, Tuple

from fastapi import HTTPException, status
import requests
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.resume_service.recommender import generate_recommendations
from app.scraping_service.injector import inject_jobs
from app.scraping_service.parser import parse_serp_jobs
from app.scraping_service.serp_service import SerpApiJobsService
from app.scraping_service.utils import build_query_candidates

logger = logging.getLogger(__name__)


async def inject_preferred_jobs_for_user(
    db: AsyncIOMotorDatabase,
    user_id: str,
    max_results: int = 20,
    refresh_recommendations: bool = True,
) -> Dict:
    """Fetch preferred jobs from SerpAPI and inject them into jobs collection."""
    profile = await db.resume_profiles.find_one(
        {"user_id": user_id},
        {"raw_text": 1, "extracted_skills": 1, "extracted_sections.summary": 1},
    )
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume profile not found for user.")

    resume_text = str(profile.get("raw_text") or "")
    extracted_skills = profile.get("extracted_skills") or []
    if not isinstance(extracted_skills, list):
        extracted_skills = []

    summary_text = ""
    sections = profile.get("extracted_sections") or {}
    if isinstance(sections, dict):
        summary_text = str(sections.get("summary") or "")

    serp_service = SerpApiJobsService()
    query_candidates = build_query_candidates(extracted_skills=extracted_skills, summary_text=summary_text)

    aggregated_jobs: List[Dict] = []
    seen_signatures: Set[Tuple[str, str, str, str]] = set()
    successful_query = query_candidates[0] if query_candidates else "entry level jobs"
    hard_error_message = None

    for query in query_candidates:
        try:
            payload = await serp_service.fetch_jobs(query=query, max_results=max_results)
        except RuntimeError as exc:
            message_lc = str(exc).lower()
            if "hasn't returned any results" in message_lc or "no results" in message_lc:
                logger.info("SerpAPI no results for query='%s'; trying fallback.", query)
                continue
            hard_error_message = str(exc)
            logger.error("SerpAPI hard error for query='%s': %s", query, exc)
            continue
        except requests.RequestException:
            hard_error_message = "Failed to fetch jobs from SerpAPI. Check API key/quota/network."
            logger.error("SerpAPI network error for query='%s'.", query)
            continue

        parsed_jobs = parse_serp_jobs(payload)
        if not parsed_jobs:
            logger.info("SerpAPI returned empty parsed jobs for query='%s'; trying fallback.", query)
            continue

        successful_query = query
        for job in parsed_jobs:
            signature = (
                str(job.get("title") or "").lower(),
                str(job.get("company") or "").lower(),
                str(job.get("location") or "").lower(),
                str(job.get("url") or "").lower(),
            )
            if signature in seen_signatures:
                continue
            seen_signatures.add(signature)
            aggregated_jobs.append(job)
            if len(aggregated_jobs) >= max_results:
                break

        if len(aggregated_jobs) >= max_results:
            break

    if not aggregated_jobs and hard_error_message:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=hard_error_message)

    jobs = aggregated_jobs
    inserted = await inject_jobs(db=db, jobs=jobs)

    refreshed = False
    if refresh_recommendations:
        try:
            await generate_recommendations(
                db=db,
                user_id=user_id,
                resume_text=resume_text,
                extracted_skills=extracted_skills,
                top_k=10,
            )
            refreshed = True
        except Exception as exc:  # pragma: no cover - recommendation refresh is optional
            logger.exception("Recommendation refresh after scraping failed user_id=%s error=%s", user_id, exc)

    return {
        "user_id": user_id,
        "query": successful_query,
        "fetched": len(jobs),
        "inserted": inserted,
        "refreshed_recommendations": refreshed,
    }


from app.scraping_service.router import router  # noqa: E402
