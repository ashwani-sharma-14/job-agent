from pydantic_settings import BaseSettings
from functools import lru_cache


RESTRICTED_COMPANIES = [
    "idea usher",
    "infralyte technologies",
    "joveo",
    "career cartz",
    "um it",
    "argo intern",
    "wake up whistle",
    "it career",
    "logical soft tech",
]


class Settings(BaseSettings):
    APP_NAME: str = "JobAgent"
    DEBUG: bool = False

    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/jobagent"

    GEMINI_API_KEY: str = "your-gemini-api-key"
    GEMINI_MODEL: str = "gemini-2.0-flash"

    UPSTASH_REDIS_REST_URL: str = "https://your-redis.upstash.io"
    UPSTASH_REDIS_REST_TOKEN: str = "your-upstash-token"

    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = "your-email@gmail.com"
    SMTP_PASSWORD: str = "your-app-password"
    NOTIFICATION_EMAIL: str = "your-email@gmail.com"

    GOOGLE_DRIVE_RESUME_URL: str = ""

    ADZUNA_APP_ID: str = ""
    ADZUNA_APP_KEY: str = ""
    RAPIDAPI_KEY: str = ""

    LLM_RPM_LIMIT: int = 25
    LLM_DAILY_LIMIT: int = 14000

    DAILY_JOB_LIMIT: int = 100
    MIN_MATCH_SCORE: float = 0.1

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
