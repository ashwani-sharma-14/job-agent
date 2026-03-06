import json
import re

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func

from app.models.models import Job, Application, JobNotification
from app.services.llm_service import invoke_llm
from app.services.resume_service import get_resume_context
from app.core.prompts import JD_ANALYSIS_PROMPT
from app.core.config import get_settings

settings = get_settings()


async def analyze_job(job: Job, resume_text: str) -> dict:
    if not job.job_description:
        return {"match_score": 0.0, "required_skills": [], "missing_skills": [], "recommendation": "skip"}

    prompt = JD_ANALYSIS_PROMPT.format(
        job_description=job.job_description[:3000],
        resume_context=resume_text,
    )
    content = await invoke_llm(prompt, temperature=0.2)

    try:
        json_match = re.search(r"\{.*\}", content, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            if "match_score" in data:
                return data
    except (json.JSONDecodeError, ValueError) as e:
        logger.error("Failed to parse analysis for '{}': {}", job.title, e)

    return {"match_score": 0.0, "required_skills": [], "missing_skills": [], "recommendation": "skip"}


async def analyze_jobs(db: AsyncSession) -> list[dict]:
    resume_ctx = await get_resume_context()
    resume_text = json.dumps(resume_ctx.model_dump(), indent=2)

    result = await db.execute(
        select(Job).where(Job.is_analyzed == False).limit(30)
    )
    jobs = result.scalars().all()

    if not jobs:
        logger.info("No unanalyzed jobs remaining")
        return []

    results = []
    low_score_ids = []

    for job in jobs:
        analysis = await analyze_job(job, resume_text)
        score = analysis.get("match_score", 0.0)

        job.is_analyzed = True

        if score < settings.MIN_MATCH_SCORE:
            low_score_ids.append(job.id)
            logger.info("Marking low-score job '{}' at {} for removal — score: {}", job.title, job.company, score)
            continue

        job.match_score = score
        job.required_skills = json.dumps(analysis.get("required_skills", []))
        job.missing_skills = json.dumps(analysis.get("missing_skills", []))

        results.append({
            "title": job.title,
            "company": job.company,
            "match_score": score,
            "recommendation": analysis.get("recommendation", ""),
            "is_fresher_friendly": analysis.get("is_fresher_friendly", False),
        })
        logger.info("Analyzed '{}' at {} — score: {}", job.title, job.company, score)

    if low_score_ids:
        await db.execute(delete(JobNotification).where(JobNotification.job_id.in_(low_score_ids)))
        await db.execute(delete(Application).where(Application.job_id.in_(low_score_ids)))
        await db.execute(delete(Job).where(Job.id.in_(low_score_ids)))
        logger.info("Removed {} low-score jobs (below {}) from database", len(low_score_ids), settings.MIN_MATCH_SCORE)

    await db.flush()
    return results


async def get_unanalyzed_count(db: AsyncSession) -> int:
    result = await db.execute(
        select(func.count()).select_from(Job).where(Job.is_analyzed == False)
    )
    return result.scalar() or 0
