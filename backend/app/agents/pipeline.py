from typing_extensions import TypedDict

from loguru import logger
from langgraph.graph import StateGraph, START, END
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.models import Job
from app.agents.job_search_agent import discover_jobs
from app.agents.jd_analysis_agent import analyze_jobs
from app.agents.application_agent import process_application


class PipelineState(TypedDict):
    jobs_discovered: list[dict]
    jobs_cleaned: list[dict]
    jobs_analyzed: list[dict]
    applications: list[dict]
    db: AsyncSession


async def job_search_node(state: PipelineState) -> dict:
    logger.info("Pipeline: Job Discovery")
    jobs = await discover_jobs(state["db"])
    return {"jobs_discovered": jobs}


async def clean_node(state: PipelineState) -> dict:
    from app.agents.job_search_agent import clean_and_store_jobs
    logger.info("Pipeline: Job Cleaning")
    jobs = await clean_and_store_jobs(state["db"])
    return {"jobs_cleaned": jobs}


async def jd_analysis_node(state: PipelineState) -> dict:
    logger.info("Pipeline: JD Analysis")
    results = await analyze_jobs(state["db"])
    return {"jobs_analyzed": results}


async def application_node(state: PipelineState) -> dict:
    logger.info("Pipeline: Application Processing")
    from app.services.redis_service import is_daily_limit_reached, increment_daily_count, get_remaining_quota

    db = state["db"]
    remaining = get_remaining_quota()

    if remaining <= 0:
        logger.info("Daily limit reached, skipping applications")
        return {"applications": []}

    result = await db.execute(
        select(Job).where(Job.is_analyzed == True, Job.match_score >= 0.1).limit(remaining)
    )
    matching_jobs = result.scalars().all()

    applications = []
    for job in matching_jobs:
        if is_daily_limit_reached():
            logger.info("Daily limit reached mid-processing, stopping")
            break

        app_result = await process_application(job, db)
        increment_daily_count()
        applications.append(app_result)

    return {"applications": applications}


def build_pipeline() -> StateGraph:
    graph = StateGraph(PipelineState)

    graph.add_node("job_search", job_search_node)
    graph.add_node("job_clean", clean_node)
    graph.add_node("jd_analysis", jd_analysis_node)
    graph.add_node("auto_apply", application_node)

    graph.add_edge(START, "job_search")
    graph.add_edge("job_search", "job_clean")
    graph.add_edge("job_clean", "jd_analysis")
    graph.add_edge("jd_analysis", "auto_apply")
    graph.add_edge("auto_apply", END)

    return graph.compile()


pipeline = build_pipeline()


async def run_discovery_pipeline(db: AsyncSession) -> dict:
    state = {
        "jobs_discovered": [],
        "jobs_cleaned": [],
        "jobs_analyzed": [],
        "applications": [],
        "db": db,
    }
    result = await job_search_node(state)
    return {
        "status": "ok",
        "message": "Job discovery complete",
        "jobs_found": len(result.get("jobs_discovered", [])),
    }


async def run_clean_pipeline(db: AsyncSession) -> dict:
    state = {
        "jobs_discovered": [],
        "jobs_cleaned": [],
        "jobs_analyzed": [],
        "applications": [],
        "db": db,
    }
    result = await clean_node(state)
    return {
        "status": "ok",
        "message": "Job cleaning complete",
        "jobs_cleaned": len(result.get("jobs_cleaned", [])),
    }


async def run_analysis_pipeline(db: AsyncSession) -> dict:
    state = {
        "jobs_discovered": [],
        "jobs_cleaned": [],
        "jobs_analyzed": [],
        "applications": [],
        "db": db,
    }
    result = await jd_analysis_node(state)
    return {
        "status": "ok",
        "message": "Job analysis complete",
        "jobs_analyzed": len(result.get("jobs_analyzed", [])),
    }


async def run_application_pipeline(db: AsyncSession) -> dict:
    state: PipelineState = {
        "jobs_discovered": [],
        "jobs_cleaned": [],
        "jobs_analyzed": [],
        "applications": [],
        "db": db,
    }
    result = await application_node(state)
    return {
        "status": "ok",
        "message": "Application processing complete",
        "applications_created": len(result.get("applications", [])),
    }


async def run_full_pipeline(db: AsyncSession) -> dict:
    state: PipelineState = {
        "jobs_discovered": [],
        "jobs_cleaned": [],
        "jobs_analyzed": [],
        "applications": [],
        "db": db,
    }

    result = await pipeline.ainvoke(state)

    return {
        "status": "ok",
        "message": "Full pipeline complete",
        "jobs_found": len(result.get("jobs_discovered", [])),
        "jobs_cleaned": len(result.get("jobs_cleaned", [])),
        "jobs_analyzed": len(result.get("jobs_analyzed", [])),
        "applications_created": len(result.get("applications", [])),
    }
