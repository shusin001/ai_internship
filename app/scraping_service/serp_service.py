"""SerpAPI client for Google Jobs scraping."""

import asyncio
import logging
from typing import Any, Dict

import requests

from app.config import settings

logger = logging.getLogger(__name__)


class SerpApiJobsService:
    def __init__(self) -> None:
        self.base_url = settings.serpapi_base_url

    async def fetch_jobs(self, query: str, max_results: int = 20) -> Dict[str, Any]:
        return await asyncio.to_thread(self._fetch_jobs_sync, query, max_results)

    def _fetch_jobs_sync(self, query: str, max_results: int = 20) -> Dict[str, Any]:
        if not settings.serpapi_api_key:
            raise RuntimeError("SERPAPI_API_KEY is not configured.")

        base_params = {
            "engine": settings.serpapi_engine,
            "q": query,
            "api_key": settings.serpapi_api_key,
            "hl": "en",
            "gl": "us",
            "num": max(5, min(int(max_results), 50)),
        }

        raw_location = (settings.serpapi_location or "").strip()
        location_candidates = [token.strip() for token in raw_location.split(",") if token.strip()]
        # Always try no-location fallback last to avoid hard failure on bad location strings.
        attempts = location_candidates + [""]

        last_exc = None
        for location in attempts:
            params = dict(base_params)
            if location and location.lower() != "remote":
                params["location"] = location
            try:
                response = requests.get(self.base_url, params=params, timeout=40)
                response.raise_for_status()
                payload = response.json()
                if isinstance(payload, dict) and payload.get("error"):
                    raise RuntimeError("SerpAPI error: {}".format(payload.get("error")))
                return payload
            except requests.HTTPError as exc:
                last_exc = exc
                status_code = exc.response.status_code if exc.response is not None else None
                # Retry with next location candidate on bad-request style failures.
                if status_code in (400, 422):
                    logger.warning(
                        "SerpAPI rejected location='%s' for query='%s'; retrying fallback.",
                        location or "<none>",
                        query,
                    )
                    continue
                logger.error("SerpAPI request failed: %s", exc)
                raise
            except requests.RequestException as exc:
                logger.error("SerpAPI request failed: %s", exc)
                raise
            except ValueError as exc:
                logger.error("SerpAPI JSON parsing failed: %s", exc)
                raise

        if last_exc is not None:
            raise last_exc
        raise RuntimeError("SerpAPI request failed unexpectedly.")
