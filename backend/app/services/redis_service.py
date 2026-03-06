from datetime import date

from upstash_redis import Redis
from loguru import logger

from app.core.config import get_settings

settings = get_settings()


_redis: Redis | None = None

DAILY_COUNTER_KEY = "jobagent:daily_count:{date}"
SEEN_JOBS_KEY = "jobagent:seen_urls"
RESUME_CACHE_KEY = "jobagent:resume_cache"
LAST_RUN_KEY = "jobagent:last_run"


def get_redis() -> Redis:
    global _redis
    if _redis:
        return _redis
    _redis = Redis(
        url=settings.UPSTASH_REDIS_REST_URL,
        token=settings.UPSTASH_REDIS_REST_TOKEN,
    )
    logger.info("Upstash Redis connected")
    return _redis


def close_redis():
    global _redis
    _redis = None
    logger.info("Upstash Redis connection released")


def get_daily_count() -> int:
    r = get_redis()
    key = DAILY_COUNTER_KEY.format(date=date.today().isoformat())
    count = r.get(key)
    return int(count) if count else 0


def increment_daily_count() -> int:
    r = get_redis()
    key = DAILY_COUNTER_KEY.format(date=date.today().isoformat())
    new_count = r.incr(key)
    if new_count == 1:
        r.expire(key, 86400)
    return new_count


def is_daily_limit_reached() -> bool:
    count = get_daily_count()
    return count >= settings.DAILY_JOB_LIMIT


def get_remaining_quota() -> int:
    count = get_daily_count()
    return max(0, settings.DAILY_JOB_LIMIT - count)


def is_job_seen(url: str) -> bool:
    if not url:
        return False
    r = get_redis()
    return r.sismember(SEEN_JOBS_KEY, url)


def mark_job_seen(url: str):
    if not url:
        return
    r = get_redis()
    r.sadd(SEEN_JOBS_KEY, url)


def cache_resume(data: str, ttl: int = 3600):
    r = get_redis()
    r.set(RESUME_CACHE_KEY, data, ex=ttl)


def get_cached_resume() -> str | None:
    r = get_redis()
    return r.get(RESUME_CACHE_KEY)


def record_pipeline_run(result: dict):
    r = get_redis()
    import json
    r.set(LAST_RUN_KEY, json.dumps({
        "timestamp": date.today().isoformat(),
        "daily_count": get_daily_count(),
        **result,
    }))


RAW_JOBS_KEY = "jobagent:raw_jobs"


def store_raw_jobs(jobs: list[dict]):
    import json
    r = get_redis()
    existing = r.get(RAW_JOBS_KEY)
    current = json.loads(existing) if existing else []
    current.extend(jobs)
    r.set(RAW_JOBS_KEY, json.dumps(current), ex=86400)
    logger.info("Stored {} raw jobs in Redis (total: {})", len(jobs), len(current))


def get_raw_jobs() -> list[dict]:
    import json
    r = get_redis()
    data = r.get(RAW_JOBS_KEY)
    if not data:
        return []
    r.delete(RAW_JOBS_KEY)
    return json.loads(data)
