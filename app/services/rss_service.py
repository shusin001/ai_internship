import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List

import feedparser

from app.config import settings
from app.utils.helpers import parse_datetime, sanitize_text, utcnow

logger = logging.getLogger(__name__)


class RSSService:
    def __init__(self) -> None:
        self.feed_url = settings.rss_feed_url or "https://remotive.com/remote-jobs/feed"

    async def fetch_jobs(self) -> List[Dict[str, Any]]:
        return await asyncio.to_thread(self._fetch_jobs_sync)

    def _fetch_jobs_sync(self) -> List[Dict[str, Any]]:
        if not self.feed_url:
            logger.warning("RSS_FEED_URL missing; skipping RSS fetch.")
            return []
        try:
            parsed = feedparser.parse(self.feed_url)
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("RSS parse failed: %s", exc)
            return []

        if getattr(parsed, "bozo", 0):
            logger.warning("RSS feed bozo flag set; entries may be incomplete.")

        jobs = []
        for entry in parsed.entries:
            normalized = self._normalize_entry(entry)
            if normalized:
                jobs.append(normalized)
        logger.info("RSS fetch completed. fetched=%s", len(jobs))
        return jobs

    def _normalize_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        title = sanitize_text(entry.get("title"))
        company = sanitize_text(entry.get("author") or entry.get("source", {}).get("title"), fallback="Unknown")
        location = sanitize_text(entry.get("location"), fallback="Remote/Unspecified")
        description = entry.get("summary") or entry.get("description") or ""

        published = parse_datetime(entry.get("published") or entry.get("updated"))
        if published is None and entry.get("published_parsed"):
            published = datetime.fromtimestamp(time.mktime(entry["published_parsed"]), tz=timezone.utc)
        posted_date = published or utcnow()

        job_url = entry.get("link")

        return {
            "title": title,
            "company": company,
            "location": location,
            "description": description,
            "salary_min": None,
            "salary_max": None,
            "employment_type": "Unknown",
            "source": "rss",
            "posted_date": posted_date,
            "url": job_url,
            "created_at": utcnow(),
            "updated_at": utcnow(),
        }
