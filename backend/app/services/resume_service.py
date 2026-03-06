import io
import json
import re
import tempfile

import httpx
import pdfplumber
from loguru import logger

from app.core.config import get_settings
from app.core.prompts import RESUME_PARSE_PROMPT
from app.services.llm_service import invoke_llm
from app.schemas.job_schema import ResumeContext

settings = get_settings()

_cached_resume: ResumeContext | None = None


def _extract_gdrive_file_id(url: str) -> str | None:
    patterns = [
        r"/file/d/([a-zA-Z0-9_-]+)",
        r"id=([a-zA-Z0-9_-]+)",
        r"/d/([a-zA-Z0-9_-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def _extract_text_from_pdf(pdf_bytes: bytes) -> str:
    text_parts = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)


async def download_resume() -> str:
    url = settings.GOOGLE_DRIVE_RESUME_URL
    if not url:
        logger.warning("No Google Drive resume URL configured")
        return ""

    file_id = _extract_gdrive_file_id(url)
    if not file_id:
        logger.error("Could not extract file ID from URL: {}", url)
        return ""

    download_url = f"https://drive.google.com/uc?export=download&id={file_id}"

    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        response = await client.get(download_url)
        response.raise_for_status()
        raw_bytes = response.content

    if raw_bytes[:5] == b"%PDF-":
        logger.info("Detected PDF resume, extracting text...")
        text = _extract_text_from_pdf(raw_bytes)
        if text.strip():
            logger.info("Extracted {} chars from PDF resume", len(text))
            return text

    text = raw_bytes.decode("utf-8", errors="ignore")

    if not text.strip() or "<html" in text.lower()[:200]:
        logger.warning("Google Drive returned HTML, trying Docs export")
        export_url = f"https://docs.google.com/document/d/{file_id}/export?format=txt"
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            response = await client.get(export_url)
            if response.status_code == 200:
                text = response.text

    logger.info("Downloaded resume: {} characters", len(text))
    return text


async def parse_resume(resume_text: str) -> ResumeContext:
    if not resume_text.strip():
        return ResumeContext()

    prompt = RESUME_PARSE_PROMPT.format(resume_text=resume_text[:5000])
    content = await invoke_llm(prompt, temperature=0.1)

    try:
        json_match = re.search(r"\{.*\}", content, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            ctx = ResumeContext(**data)
            logger.info("Parsed resume: {} skills, {} projects", len(ctx.skills), len(ctx.projects))
            return ctx
    except (json.JSONDecodeError, ValueError) as e:
        logger.error("Failed to parse resume LLM response: {}", e)

    return ResumeContext()


async def get_resume_context() -> ResumeContext:
    global _cached_resume
    if _cached_resume and _cached_resume.skills:
        return _cached_resume

    from app.services.redis_service import get_cached_resume, cache_resume

    cached = get_cached_resume()
    if cached:
        try:
            _cached_resume = ResumeContext(**json.loads(cached))
            if _cached_resume.skills:
                logger.info("Resume loaded from Redis cache")
                return _cached_resume
        except (json.JSONDecodeError, ValueError):
            pass

    resume_text = await download_resume()
    _cached_resume = await parse_resume(resume_text)

    if _cached_resume.skills:
        cache_resume(json.dumps(_cached_resume.model_dump()), ttl=3600)

    return _cached_resume
