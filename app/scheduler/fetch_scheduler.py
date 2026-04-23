import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings
from app.database import get_database
from app.services.job_service import JobService

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="UTC")


async def run_ingestion_cycle() -> None:
    try:
        service = JobService(get_database())
        summary = await service.ingest_all_sources()
        logger.info("Scheduled ingestion complete: %s", summary)
    except Exception as exc:  # pragma: no cover - defensive startup/scheduler handling
        logger.exception("Scheduled ingestion failed: %s", exc)


def start_scheduler() -> None:
    if scheduler.running:
        return
    scheduler.add_job(
        run_ingestion_cycle,
        trigger="interval",
        hours=settings.fetch_interval_hours,
        id="job_ingestion_cycle",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    logger.info("Scheduler started. interval_hours=%s", settings.fetch_interval_hours)


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped.")
