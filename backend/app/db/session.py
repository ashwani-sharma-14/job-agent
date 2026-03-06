import re
import ssl as ssl_module

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()


def _clean_url(url: str) -> str:
    url = re.sub(r"[?&]sslmode=[^&]*", "", url)
    url = re.sub(r"[?&]channel_binding=[^&]*", "", url)
    if "?" in url and url.endswith("?"):
        url = url.rstrip("?")
    return url


_db_url = _clean_url(settings.DATABASE_URL)
_ssl_context = ssl_module.create_default_context()
_ssl_context.check_hostname = False
_ssl_context.verify_mode = ssl_module.CERT_NONE

engine = create_async_engine(
    _db_url,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    connect_args={"ssl": _ssl_context},
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
