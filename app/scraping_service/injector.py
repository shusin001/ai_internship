"""MongoDB injection logic for scraped jobs."""

from typing import Any, Dict, List

from motor.motor_asyncio import AsyncIOMotorDatabase


async def inject_jobs(db: AsyncIOMotorDatabase, jobs: List[Dict[str, Any]]) -> int:
    """Insert only new jobs using existing unique signature constraints."""
    inserted = 0

    for job in jobs:
        signature_filter = {
            "title": job.get("title"),
            "company": job.get("company"),
            "location": job.get("location"),
            "source": job.get("source"),
        }
        result = await db.jobs.update_one(
            signature_filter,
            {"$setOnInsert": job},
            upsert=True,
        )
        if result.upserted_id is not None:
            inserted += 1

    return inserted
