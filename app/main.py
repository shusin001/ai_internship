import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import app.resume_service as resume_service
import app.guidance_service as guidance_service
import app.scraping_service as scraping_service

from app.config import settings
from app.database import close_mongo_connection, connect_to_mongo, init_indexes
from app.routes.analytics import router as analytics_router
from app.routes.jobs import router as jobs_router
from app.routes.users import router as users_router
from app.scheduler.fetch_scheduler import run_ingestion_cycle, start_scheduler, stop_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await connect_to_mongo()
    await init_indexes()
    start_scheduler()
    asyncio.create_task(run_ingestion_cycle())
    logger.info("Application started successfully.")
    try:
        yield
    finally:
        stop_scheduler()
        await close_mongo_connection()
        logger.info("Application shutdown complete.")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=settings.app_description,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_router)
app.include_router(jobs_router)
app.include_router(analytics_router)
app.include_router(resume_service.router, prefix="/resume-service", tags=["Resume Service"])
app.include_router(guidance_service.router, prefix="/guidance", tags=["Guidance"])
app.include_router(scraping_service.router, prefix="/scraping-injection", tags=["Scraping Injection"])


@app.get("/", tags=["Health"], summary="API health endpoint")
async def root() -> dict:
    return {
        "message": "ReCompass backend is running.",
        "docs": "/docs",
    }
