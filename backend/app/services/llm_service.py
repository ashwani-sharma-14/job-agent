import asyncio
import time
from datetime import date

from langchain_google_genai import ChatGoogleGenerativeAI
from loguru import logger

from app.core.config import get_settings
from app.services.redis_service import get_redis

settings = get_settings()

_call_timestamps: list[float] = []
_rate_lock = asyncio.Lock()

RPM_LIMIT = settings.LLM_RPM_LIMIT
DAILY_LIMIT = settings.LLM_DAILY_LIMIT
DAILY_LLM_KEY = "jobagent:llm_daily:{date}"


def _get_daily_llm_count() -> int:
    r = get_redis()
    key = DAILY_LLM_KEY.format(date=date.today().isoformat())
    count = r.get(key)
    return int(count) if count else 0


def _increment_daily_llm_count():
    r = get_redis()
    key = DAILY_LLM_KEY.format(date=date.today().isoformat())
    new = r.incr(key)
    if new == 1:
        r.expire(key, 86400)
    return new


async def _wait_for_rate_limit():
    async with _rate_lock:
        daily = _get_daily_llm_count()
        if daily >= DAILY_LIMIT:
            logger.warning("Daily LLM limit ({}) reached, skipping", DAILY_LIMIT)
            raise RuntimeError("Daily LLM request limit reached")

        now = time.time()
        _call_timestamps[:] = [t for t in _call_timestamps if now - t < 60]

        if len(_call_timestamps) >= RPM_LIMIT:
            oldest = _call_timestamps[0]
            wait_time = 60 - (now - oldest) + 1.0
            logger.info("RPM limit hit, waiting {:.1f}s", wait_time)
            await asyncio.sleep(wait_time)

        _call_timestamps.append(time.time())
        _increment_daily_llm_count()


def get_llm(temperature: float = 0.3) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        google_api_key=settings.GEMINI_API_KEY,
        temperature=temperature,
    )


async def invoke_llm(prompt: str, temperature: float = 0.3) -> str:
    await _wait_for_rate_limit()
    llm = get_llm(temperature)
    result = await llm.ainvoke(prompt)
    return result.content
