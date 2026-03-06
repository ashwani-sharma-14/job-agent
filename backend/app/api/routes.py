from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

router = APIRouter()


@router.get("/jobs")
async def list_jobs(db: AsyncSession = Depends(get_db)):
    from app.models.models import Job
    from sqlalchemy import select

    result = await db.execute(select(Job).order_by(Job.created_at.desc()))
    jobs = result.scalars().all()
    return [
        {
            "id": str(j.id),
            "title": j.title,
            "company": j.company,
            "location": j.location,
            "source_url": j.source_url,
            "created_at": j.created_at.isoformat() if j.created_at else None,
        }
        for j in jobs
    ]


@router.post("/agent/discover")
async def discover_jobs(db: AsyncSession = Depends(get_db)):
    from app.agents.pipeline import run_discovery_pipeline

    result = await run_discovery_pipeline(db)
    await db.commit()
    return result


@router.post("/agent/clean")
async def clean_jobs(db: AsyncSession = Depends(get_db)):
    from app.agents.pipeline import run_clean_pipeline

    result = await run_clean_pipeline(db)
    await db.commit()
    return result


@router.post("/agent/analyze")
async def analyze_jobs(db: AsyncSession = Depends(get_db)):
    from app.agents.pipeline import run_analysis_pipeline

    result = await run_analysis_pipeline(db)
    await db.commit()
    return result


@router.post("/agent/apply")
async def apply_to_jobs(db: AsyncSession = Depends(get_db)):
    from app.agents.pipeline import run_full_pipeline

    result = await run_full_pipeline(db)
    await db.commit()
    return result
