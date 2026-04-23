from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING, TEXT

from app.config import settings

client: Optional[AsyncIOMotorClient] = None


async def connect_to_mongo() -> None:
    global client
    if not settings.mongodb_uri:
        raise RuntimeError("MONGODB_URI is not configured.")
    client = AsyncIOMotorClient(settings.mongodb_uri)


async def close_mongo_connection() -> None:
    global client
    if client is not None:
        client.close()
    client = None


def get_database() -> AsyncIOMotorDatabase:
    if client is None:
        raise RuntimeError("Database not initialized. Call connect_to_mongo first.")
    return client[settings.mongodb_db_name]


async def init_indexes() -> None:
    db = get_database()

    await db.jobs.create_index(
        [("title", ASCENDING), ("company", ASCENDING), ("location", ASCENDING), ("source", ASCENDING)],
        unique=True,
        name="unique_job_signature",
    )
    await db.jobs.create_index([("title", TEXT), ("description", TEXT)], name="text_search_idx")
    await db.jobs.create_index([("posted_date", DESCENDING)], name="posted_date_idx")
    await db.jobs.create_index([("source", ASCENDING)], name="source_idx")
    await db.jobs.create_index([("location", ASCENDING)], name="location_idx")
    await db.jobs.create_index([("company", ASCENDING)], name="company_idx")

    await db.users.create_index([("email", ASCENDING)], unique=True, name="unique_user_email")
    await db.resume_profiles.create_index([("user_id", ASCENDING)], unique=True, name="unique_resume_user_id")
