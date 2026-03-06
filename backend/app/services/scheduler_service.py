from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

from app.db.session import async_session

scheduler = AsyncIOScheduler()


async def run_discovery():
    logger.info("Scheduled: Job Discovery")
    from app.agents.pipeline import run_discovery_pipeline

    async with async_session() as db:
        try:
            result = await run_discovery_pipeline(db)
            await db.commit()
            logger.info("Discovery complete: {}", result)
        except Exception as e:
            await db.rollback()
            logger.error("Discovery failed: {}", e)


async def run_clean_cycle():
    logger.info("Scheduled: Job Cleaning")
    from app.agents.pipeline import run_clean_pipeline

    async with async_session() as db:
        try:
            result = await run_clean_pipeline(db)
            await db.commit()
            logger.info("Cleaning complete: {}", result)
        except Exception as e:
            await db.rollback()
            logger.error("Cleaning failed: {}", e)


async def run_analysis_cycle():
    logger.info("Scheduled: Analysis Cycle")
    from app.agents.jd_analysis_agent import analyze_jobs, get_unanalyzed_count

    async with async_session() as db:
        try:
            remaining = await get_unanalyzed_count(db)
            if remaining == 0:
                logger.info("No unanalyzed jobs, skipping")
                return

            results = await analyze_jobs(db)
            await db.commit()

            remaining_after = await get_unanalyzed_count(db)
            logger.info("Analysis cycle done: {} analyzed, {} remaining", len(results), remaining_after)
        except Exception as e:
            await db.rollback()
            logger.error("Analysis cycle failed: {}", e)


async def run_application():
    logger.info("Scheduled: Application Processing")
    from app.agents.pipeline import run_application_pipeline

    async with async_session() as db:
        try:
            result = await run_application_pipeline(db)
            await db.commit()
            logger.info("Application processing complete: {}", result)
        except Exception as e:
            await db.rollback()
            logger.error("Application processing failed: {}", e)


def start_scheduler():
    scheduler.add_job(
        run_discovery,
        "cron",
        hour="0,6,12,18",
        minute=0,
        id="job_discovery",
        replace_existing=True,
    )

    scheduler.add_job(
        run_clean_cycle,
        "cron",
        hour="1,7,13,19",
        minute=0,
        id="job_cleaning",
        replace_existing=True,
    )

    scheduler.add_job(
        run_analysis_cycle,
        "cron",
        hour="2,8,14,20",
        minute=0,
        id="job_analysis",
        replace_existing=True,
    )

    scheduler.add_job(
        run_application,
        "cron",
        hour="3,9,15,21",
        minute=0,
        id="job_application",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(
        "Scheduler started — 4-phase cycle: "
        "discovery(0,6,12,18) | "
        "clean(1,7,13,19) | "
        "analysis(2,8,14,20) | "
        "apply(3,9,15,21)"
    )


def stop_scheduler():
    scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped")
