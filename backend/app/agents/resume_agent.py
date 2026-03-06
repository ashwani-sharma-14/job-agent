import json

from loguru import logger

from app.services.llm_service import invoke_llm
from app.services.resume_service import get_resume_context
from app.core.prompts import RESUME_REWRITE_PROMPT, COVER_LETTER_PROMPT


async def rewrite_resume(job_description: str) -> str:
    resume_ctx = await get_resume_context()
    resume_text = json.dumps(resume_ctx.model_dump(), indent=2)

    prompt = RESUME_REWRITE_PROMPT.format(
        resume_context=resume_text,
        job_description=job_description[:3000],
    )
    content = await invoke_llm(prompt, temperature=0.4)
    logger.info("Resume rewritten for JD")
    return content


async def generate_cover_letter(
    job_title: str, company: str, job_description: str
) -> str:
    resume_ctx = await get_resume_context()
    resume_text = json.dumps(resume_ctx.model_dump(), indent=2)

    prompt = COVER_LETTER_PROMPT.format(
        job_title=job_title,
        company=company,
        job_description=job_description[:2000],
        resume_context=resume_text,
    )
    content = await invoke_llm(prompt, temperature=0.5)
    logger.info("Cover letter generated for {} at {}", job_title, company)
    return content
