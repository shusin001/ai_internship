import asyncio
import logging
import math
from typing import Any, Dict, Optional, Union

from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorDatabase
import requests

from app.models.job_model import build_job_document
from app.scraping_service.parser import parse_serp_jobs
from app.scraping_service.serp_service import SerpApiJobsService
from app.services.rss_service import RSSService
from app.services.usajobs_service import USAJobsService
from app.utils.helpers import serialize_mongo_document
from app.config import settings

logger = logging.getLogger(__name__)


class JobService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.usajobs_service = USAJobsService()
        self.rss_service = RSSService()
        self.serpapi_service = SerpApiJobsService()

    async def ingest_from_usajobs(self) -> Dict[str, Union[int, str]]:
        jobs = await self.usajobs_service.fetch_jobs()
        inserted = await self.store_jobs(jobs)
        return {"source": "usajobs", "fetched": len(jobs), "inserted": inserted}

    async def ingest_from_rss(self) -> Dict[str, Union[int, str]]:
        jobs = await self.rss_service.fetch_jobs()
        inserted = await self.store_jobs(jobs)
        return {"source": "rss", "fetched": len(jobs), "inserted": inserted}

    async def ingest_from_serpapi(self) -> Dict[str, Union[int, str]]:
        if not settings.serpapi_api_key:
            logger.warning("SERPAPI_API_KEY not configured; skipping SerpAPI ingestion.")
            return {"source": "serpapi", "fetched": 0, "inserted": 0}

        queries = [token.strip() for token in settings.serpapi_keywords.split(",") if token.strip()]
        if not queries:
            queries = ["entry level jobs"]

        aggregated_jobs: list[Dict[str, Any]] = []
        seen_signatures: set[tuple[str, str, str, str]] = set()

        for query in queries:
            try:
                payload = await self.serpapi_service.fetch_jobs(query=query, max_results=20)
            except RuntimeError as exc:
                message_lc = str(exc).lower()
                if "hasn't returned any results" in message_lc or "no results" in message_lc:
                    logger.info("SerpAPI returned no results for query='%s'.", query)
                    continue
                logger.error("SerpAPI ingestion failed for query='%s': %s", query, exc)
                continue
            except requests.RequestException:
                logger.error("SerpAPI network error for query='%s'.", query)
                continue

            parsed_jobs = parse_serp_jobs(payload)
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

        inserted = await self.store_jobs(aggregated_jobs)
        return {"source": "serpapi", "fetched": len(aggregated_jobs), "inserted": inserted}

    async def ingest_all_sources(self) -> Dict[str, Union[Dict[str, Union[int, str]], int]]:
        usajobs_data, rss_data, serpapi_data = await asyncio.gather(
            self.ingest_from_usajobs(),
            self.ingest_from_rss(),
            self.ingest_from_serpapi(),
        )
        total_inserted = int(usajobs_data["inserted"]) + int(rss_data["inserted"]) + int(serpapi_data["inserted"])
        return {
            "usajobs": usajobs_data,
            "rss": rss_data,
            "serpapi": serpapi_data,
            "total_inserted": total_inserted,
        }

    async def store_jobs(self, jobs: list[Dict[str, Any]]) -> int:
        inserted = 0
        for raw_job in jobs:
            document = build_job_document(raw_job)
            signature_filter = {
                "title": document["title"],
                "company": document["company"],
                "location": document["location"],
                "source": document["source"],
            }
            result = await self.db.jobs.update_one(
                signature_filter,
                {"$setOnInsert": document},
                upsert=True,
            )
            if result.upserted_id is not None:
                inserted += 1
        logger.info("Jobs stored. new=%s", inserted)
        return inserted

    async def list_jobs(
        self,
        keyword: Optional[str] = None,
        location: Optional[str] = None,
        employment_type: Optional[str] = None,
        min_salary: Optional[float] = None,
        max_salary: Optional[float] = None,
        page: int = 1,
        limit: int = 10,
    ) -> Dict[str, Any]:
        query: Dict[str, Any] = {}
        filters: list[Dict[str, Any]] = []

        if keyword:
            filters.append({"$text": {"$search": keyword}})
        if location:
            filters.append({"location": {"$regex": location, "$options": "i"}})
        if employment_type:
            filters.append({"employment_type": {"$regex": f"^{employment_type}$", "$options": "i"}})
        if min_salary is not None:
            filters.append(
                {
                    "$or": [
                        {"salary_min": {"$gte": min_salary}},
                        {"salary_max": {"$gte": min_salary}},
                    ]
                }
            )
        if max_salary is not None:
            filters.append(
                {
                    "$or": [
                        {"salary_min": {"$lte": max_salary}},
                        {"salary_max": {"$lte": max_salary}},
                    ]
                }
            )

        if filters:
            query = {"$and": filters}

        page = max(1, page)
        limit = min(max(1, limit), 100)
        skip = (page - 1) * limit

        cursor = self.db.jobs.find(query).sort("posted_date", -1).skip(skip).limit(limit)
        documents = await cursor.to_list(length=limit)
        total = await self.db.jobs.count_documents(query)
        total_pages = math.ceil(total / limit) if total else 0

        return {
            "items": [serialize_mongo_document(doc) for doc in documents],
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages,
        }

    async def get_job_by_id(self, job_id: str) -> Optional[Dict[str, Any]]:
        try:
            object_id = ObjectId(job_id)
        except InvalidId:
            return None
        doc = await self.db.jobs.find_one({"_id": object_id})
        return serialize_mongo_document(doc) if doc else None

    async def save_job_for_user(self, user_id: str, job_id: str) -> bool:
        try:
            user_object_id = ObjectId(user_id)
            job_object_id = ObjectId(job_id)
        except InvalidId:
            return False

        job = await self.db.jobs.find_one({"_id": job_object_id}, {"_id": 1})
        if job is None:
            return False

        result = await self.db.users.update_one(
            {"_id": user_object_id},
            {"$addToSet": {"saved_jobs": job_object_id}},
        )
        return result.matched_count == 1

    async def get_saved_jobs_for_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        try:
            user_object_id = ObjectId(user_id)
        except InvalidId:
            return None

        user = await self.db.users.find_one({"_id": user_object_id}, {"saved_jobs": 1})
        if user is None:
            return None

        saved_job_ids = user.get("saved_jobs", [])
        jobs = []
        if saved_job_ids:
            cursor = self.db.jobs.find({"_id": {"$in": saved_job_ids}}).sort("posted_date", -1)
            jobs = [serialize_mongo_document(doc) for doc in await cursor.to_list(length=500)]

        return {
            "user_id": user_id,
            "total_saved_jobs": len(jobs),
            "jobs": jobs,
        }

    async def get_total_jobs(self) -> Dict[str, int]:
        total = await self.db.jobs.count_documents({})
        return {"total_jobs": total}

    async def get_jobs_by_source(self) -> list[Dict[str, Any]]:
        pipeline = [
            {"$group": {"_id": "$source", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        results = await self.db.jobs.aggregate(pipeline).to_list(length=20)
        return [{"source": item["_id"], "count": item["count"]} for item in results]

    async def get_top_locations(self, limit: int = 10) -> list[Dict[str, Any]]:
        pipeline = [
            {"$group": {"_id": "$location", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": limit},
        ]
        results = await self.db.jobs.aggregate(pipeline).to_list(length=limit)
        return [{"location": item["_id"], "count": item["count"]} for item in results]

    async def get_top_companies(self, limit: int = 10) -> list[Dict[str, Any]]:
        pipeline = [
            {"$group": {"_id": "$company", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": limit},
        ]
        results = await self.db.jobs.aggregate(pipeline).to_list(length=limit)
        return [{"company": item["_id"], "count": item["count"]} for item in results]
