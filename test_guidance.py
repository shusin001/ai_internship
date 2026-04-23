import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

async def main():
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.mongodb_db_name]
    
    user = await db.users.find_one()
    job = await db.jobs.find_one()
    
    print(f"User ID: {user['_id'] if user else 'None'}")
    print(f"Job ID: {job['_id'] if job else 'None'}")

if __name__ == "__main__":
    asyncio.run(main())
