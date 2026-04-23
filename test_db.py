import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

async def main():
    client = AsyncIOMotorClient(settings.mongodb_uri, serverSelectionTimeoutMS=10000)
    try:
        await client.admin.command("ping")
        print("MongoDB ping: OK")
        print("Configured DB:", settings.mongodb_db_name)

        # List all databases
        dbs = await client.list_database_names()
        print("Databases:", dbs)

        # Check configured DB
        db = client[settings.mongodb_db_name]
        collections = await db.list_collection_names()
        print(f"\nCollections in {settings.mongodb_db_name}:", collections)

        # Check simple counts
        for coll in ["users", "jobs", "resume_profiles", "guidance_reports"]:
            count = await db[coll].count_documents({})
            print(f"Count for {coll}: {count}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(main())
