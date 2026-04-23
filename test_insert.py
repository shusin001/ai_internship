import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
from app.config import settings

async def main():
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.mongodb_db_name]
    
    # Insert a dummy record to force collection creation
    test_doc = {
        "user_id": "test_user_id",
        "job_id": "test_job_id",
        "missing_skills": ["python"],
        "gap_percentage": 10.0,
        "roadmap": {},
        "strategy": {},
        "resource_links": [],
        "llm_refined": False,
        "llm_summary": None,
        "llm_daily_remaining": 3,
        "created_at": datetime.now(timezone.utc),
    }
    
    result = await db.guidance_reports.insert_one(test_doc)
    print(f"Inserted test guidance report with ID: {result.inserted_id}")
    
    # Verify collection exists now
    collections = await db.list_collection_names()
    print("Collections now:", collections)
    
    # Delete the test record
    await db.guidance_reports.delete_one({"_id": result.inserted_id})
    print("Deleted test record")

if __name__ == "__main__":
    asyncio.run(main())
