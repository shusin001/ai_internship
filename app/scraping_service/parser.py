"""Parse SerpAPI Google Jobs payload into normalized job documents."""

from datetime import datetime, timezone
from typing import Any, Dict, List

from app.scraping_service.utils import safe_text


def _extract_job_url(job: Dict[str, Any]) -> str:
    apply_options = job.get("apply_options") or []
    if isinstance(apply_options, list):
        for option in apply_options:
            if isinstance(option, dict):
                link = safe_text(option.get("link"))
                if link:
                    return link

    related_links = job.get("related_links") or []
    if isinstance(related_links, list):
        for option in related_links:
            if isinstance(option, dict):
                link = safe_text(option.get("link"))
                if link:
                    return link

    share_link = safe_text(job.get("share_link"))
    return share_link


def parse_serp_jobs(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Parse SerpAPI result payload into app job schema."""
    jobs_raw = payload.get("jobs_results") or payload.get("jobs") or []
    if not isinstance(jobs_raw, list):
        return []

    parsed: List[Dict[str, Any]] = []
    now = datetime.now(timezone.utc)

    for item in jobs_raw:
        if not isinstance(item, dict):
            continue

        title = safe_text(item.get("title"))
        company = safe_text(item.get("company_name") or item.get("company"))
        location = safe_text(item.get("location") or item.get("detected_extensions", {}).get("location"))
        if not company:
            company = "Unknown Company"
        if not location:
            location = "Remote/Unspecified"

        highlights = item.get("job_highlights") or []
        highlights_text = []
        if isinstance(highlights, list):
            for block in highlights:
                if isinstance(block, dict):
                    bullets = block.get("items") or []
                    if isinstance(bullets, list):
                        highlights_text.extend([safe_text(entry) for entry in bullets if safe_text(entry)])

        description = safe_text(item.get("description"))
        if highlights_text:
            description = "{}\n{}".format(description, "\n".join(highlights_text)).strip()

        if not title:
            continue

        parsed.append(
            {
                "title": title,
                "company": company,
                "location": location,
                "description": description,
                "salary_min": None,
                "salary_max": None,
                "employment_type": "Unknown",
                "source": "serpapi",
                "posted_date": now,
                "url": _extract_job_url(item),
                "created_at": now,
                "updated_at": now,
            }
        )

    return parsed
