import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.core.config import get_settings
from app.api.routes import router


settings = get_settings()

logger.remove()
logger.add(
    sys.stderr,
    level="DEBUG" if settings.DEBUG else "INFO",
    format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | <cyan>{name}</cyan> - <level>{message}</level>",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting {}", settings.APP_NAME)

    from app.db.session import engine
    from app.models.models import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ready")

    from app.services.scheduler_service import start_scheduler, stop_scheduler
    from app.services.redis_service import get_redis, close_redis

    get_redis()
    start_scheduler()

    yield

    stop_scheduler()
    close_redis()

    from app.db.session import engine as _engine

    await _engine.dispose()
    logger.info("Shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered job application automation backend",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
async def health():
    from app.services.redis_service import get_daily_count, get_remaining_quota

    return {
        "status": "ok",
        "daily_jobs_processed": get_daily_count(),
        "daily_quota_remaining": get_remaining_quota(),
    }