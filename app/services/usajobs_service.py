import asyncio
import logging
from typing import Any, Dict, List

import requests

from app.config import settings
from app.utils.helpers import parse_datetime, parse_salary_number, sanitize_text, utcnow

logger = logging.getLogger(__name__)


class USAJobsService:
    def __init__(self) -> None:
        self.base_url = settings.usajobs_base_url

    async def fetch_jobs(self) -> List[Dict[str, Any]]:
        if not settings.usajobs_api_key or not settings.usajobs_user_agent:
            logger.warning("USAJOBS credentials not fully configured; skipping fetch.")
            return []

        return await asyncio.to_thread(self._fetch_jobs_sync)

    def _fetch_jobs_sync(self) -> List[Dict[str, Any]]:
        keywords = [token.strip() for token in settings.usajobs_keyword.split(",") if token.strip()]
        if not keywords:
            keywords = [""]

        all_jobs: List[Dict[str, Any]] = []
        seen_signatures = set()

        for keyword in keywords:
            fetched = self._fetch_jobs_for_keyword(keyword)
            for job in fetched:
                signature = (
                    job.get("title"),
                    job.get("company"),
                    job.get("location"),
                    job.get("url"),
                )
                if signature in seen_signatures:
                    continue
                seen_signatures.add(signature)
                all_jobs.append(job)

        logger.info("USAJOBS multi-keyword fetch completed. keywords=%s fetched=%s", len(keywords), len(all_jobs))
        return all_jobs

    def _fetch_jobs_for_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        headers = {
            "Host": settings.usajobs_api_host,
            "User-Agent": settings.usajobs_user_agent,
            "Authorization-Key": settings.usajobs_api_key,
        }
        params = {
            "ResultsPerPage": settings.usajobs_results_per_page,
        }
        if keyword:
            params["Keyword"] = keyword
        if settings.usajobs_location:
            params["LocationName"] = settings.usajobs_location

        try:
            response = requests.get(self.base_url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException as exc:
            logger.error("USAJOBS request failed: %s", exc)
            return []
        except ValueError as exc:
            logger.error("USAJOBS JSON parse failed: %s", exc)
            return []

        items = (
            payload.get("SearchResult", {})
            .get("SearchResultItems", [])
        )
        normalized = [self._normalize_item(item) for item in items]
        jobs = [job for job in normalized if job]
        logger.info("USAJOBS fetch completed. keyword=%s fetched=%s", keyword or "<none>", len(jobs))
        return jobs

    def _normalize_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        descriptor = item.get("MatchedObjectDescriptor", {})

        title = sanitize_text(descriptor.get("PositionTitle"))
        company = sanitize_text(descriptor.get("OrganizationName"))
        location = sanitize_text(descriptor.get("PositionLocationDisplay"))

        details = descriptor.get("UserArea", {}).get("Details", {})
        description = (
            details.get("JobSummary")
            or details.get("MajorDuties")
            or descriptor.get("QualificationSummary")
            or ""
        )

        remuneration = descriptor.get("PositionRemuneration", [])
        salary_min = parse_salary_number(remuneration[0].get("MinimumRange")) if remuneration else None
        salary_max = parse_salary_number(remuneration[0].get("MaximumRange")) if remuneration else None

        schedules = descriptor.get("PositionSchedule", [])
        employment_type = sanitize_text(schedules[0].get("Name"), fallback="Unknown") if schedules else "Unknown"

        posted_date = parse_datetime(descriptor.get("PublicationStartDate")) or utcnow()
        job_url = descriptor.get("PositionURI")

        return {
            "title": title,
            "company": company,
            "location": location,
            "description": description,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "employment_type": employment_type,
            "source": "usajobs",
            "posted_date": posted_date,
            "url": job_url,
            "created_at": utcnow(),
            "updated_at": utcnow(),
        }
