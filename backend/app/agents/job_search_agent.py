from urllib.parse import quote_plus
from datetime import datetime, timezone, timedelta

import httpx
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Job
from app.services.scraper_service import fetch_page, extract_job_listings, extract_linkedin_jd, extract_text
from app.core.config import get_settings, RESTRICTED_COMPANIES

settings = get_settings()

SEARCH_QUERIES = [
    "software developer fresher India",
    "full stack developer intern India",
    "python developer entry level India",
    "react developer fresher India",
    "backend developer intern India",
    "MERN stack developer fresher India",
    "junior software engineer India",
]

SENIOR_KEYWORDS = [
    "senior", "staff", "principal", "lead", "director",
    "vp", "head of", "10+ years", "8+ years", "7+ years",
    "6+ years", "5+ years", "manager","2+ Years","1+ year","3+ years"
]

IRRELEVANT_KEYWORDS = [
    "content writer", "social media", "coach", "tutor", "teacher", 
    "hr", "human resources", "sales", "marketing", "recruiter", 
    "accountant", "finance", "driver", "copywriter", "seo",
    "customer support", "customer service", "data entry", "bpo",
    "telesales", "telecaller", "business analyst", "product manager"
]

RELEVANT_KEYWORDS = [
    "software", "developer", "engineer", "programmer", "coder",
    "full stack", "fullstack", "frontend", "backend", "web",
    "python", "react", "node", "javascript",
    "intern", "fresher", "junior", "sde"
]

MAX_JD_LENGTH = 3000


def _is_restricted_company(company: str) -> bool:
    company_lower = company.lower().strip()
    return any(restricted in company_lower for restricted in RESTRICTED_COMPANIES)


def _is_senior_role(title: str) -> bool:
    title_lower = title.lower()
    return any(kw in title_lower for kw in SENIOR_KEYWORDS)


def _is_relevant_role(title: str) -> bool:
    title_lower = title.lower()
    
    if any(kw in title_lower for kw in IRRELEVANT_KEYWORDS):
        return False
        
    return any(kw in title_lower for kw in RELEVANT_KEYWORDS)


def _is_recent(date_str: str, max_days: int = 7) -> bool:
    if not date_str:
        return True
    try:
        posted = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        cutoff = datetime.now(timezone.utc) - timedelta(days=max_days)
        return posted >= cutoff
    except (ValueError, TypeError):
        return True


async def search_jobs_on_linkedin(query: str, max_days: int = 1) -> list[dict]:
    encoded = quote_plus(query)
    # r86400 = past 24 hours, r604800 = past week
    time_filter = f"r{max_days * 86400}"
    url = f"https://www.linkedin.com/jobs/search/?keywords={encoded}&location=India&geoId=102713980&f_E=1%2C2&f_TPR={time_filter}&sortBy=DD"
    
    try:
        html = await fetch_page(url)
        listings = extract_job_listings(html)
        for listing in listings:
            listing["source"] = "LinkedIn"
            listing["location"] = "India"
            listing["description"] = "" # Linkdin descriptions need secondary scrape
        logger.info("LinkedIn '{}': found {} jobs", query, len(listings))
        return listings
    except Exception as e:
        logger.error("LinkedIn scrape failed for '{}': {}", query, e)
        return []


async def search_remotive() -> list[dict]:
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get("https://remotive.com/api/remote-jobs?category=software-dev&limit=50")
            response.raise_for_status()
            data = response.json()

        jobs = []
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)

        for item in data.get("jobs", []):
            try:
                pub_date = datetime.fromisoformat(item.get("publication_date", "").replace("Z", "+00:00"))
                if pub_date < cutoff:
                    continue
            except (ValueError, TypeError):
                pass

            jobs.append({
                "title": item.get("title", ""),
                "company": item.get("company_name", "Unknown"),
                "link": item.get("url", ""),
                "source": "Remotive",
                "location": item.get("candidate_required_location", "Remote"),
                "description": item.get("description", "")[:MAX_JD_LENGTH],
            })

        logger.info("Remotive: found {} recent jobs", len(jobs))
        return jobs
    except Exception as e:
        logger.error("Remotive API failed: {}", e)
        return []


async def search_jobicy() -> list[dict]:
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get("https://jobicy.com/api/v2/remote-jobs?count=50&tag=python,javascript,react,node")
            response.raise_for_status()
            data = response.json()

        jobs = []
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)

        for item in data.get("jobs", []):
            try:
                pub_date = datetime.fromisoformat(item.get("pubDate", "").replace("Z", "+00:00"))
                if pub_date < cutoff:
                    continue
            except (ValueError, TypeError):
                pass

            jobs.append({
                "title": item.get("jobTitle", ""),
                "company": item.get("companyName", "Unknown"),
                "link": item.get("url", ""),
                "source": "Jobicy",
                "location": item.get("jobGeo", "Remote"),
                "description": item.get("jobDescription", "")[:MAX_JD_LENGTH],
            })

        logger.info("Jobicy: found {} recent jobs", len(jobs))
        return jobs
    except Exception as e:
        logger.error("Jobicy API failed: {}", e)
        return []


async def search_adzuna() -> list[dict]:
    if not settings.ADZUNA_APP_ID or not settings.ADZUNA_APP_KEY:
        logger.warning("Adzuna API keys not configured, skipping")
        return []
    try:
        url = "https://api.adzuna.com/v1/api/jobs/in/search/1"
        params = {
            "app_id": settings.ADZUNA_APP_ID,
            "app_key": settings.ADZUNA_APP_KEY,
            "results_per_page": 50,
            "what": "software developer",
            "max_days_old": 7,
            "content-type": "application/json",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            res = await client.get(url, params=params)
            res.raise_for_status()
            data = res.json()

        jobs = []
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)

        for item in data.get("results", []):
            try:
                created = datetime.fromisoformat(item.get("created", "").replace("Z", "+00:00"))
                if created < cutoff:
                    continue
            except (ValueError, TypeError):
                pass

            jobs.append({
                "title": item.get("title", ""),
                "company": item.get("company", {}).get("display_name", "Unknown"),
                "link": item.get("redirect_url", ""),
                "source": "Adzuna",
                "location": item.get("location", {}).get("display_name", "India"),
                "description": item.get("description", "")[:MAX_JD_LENGTH],
            })

        logger.info("Adzuna: found {} jobs", len(jobs))
        return jobs
    except Exception as e:
        logger.error("Adzuna API failed: {}", e)
        return []


async def search_arbeitnow() -> list[dict]:
    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            res = await client.get("https://www.arbeitnow.com/api/job-board-api")
            res.raise_for_status()
            data = res.json()

        jobs = []
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)

        for item in data.get("data", []):
            try:
                created_at = item.get("created_at", 0)
                if isinstance(created_at, (int, float)):
                    posted = datetime.fromtimestamp(created_at, tz=timezone.utc)
                else:
                    posted = datetime.fromisoformat(str(created_at).replace("Z", "+00:00"))
                if posted < cutoff:
                    continue
            except (ValueError, TypeError, OSError):
                pass

            jobs.append({
                "title": item.get("title", ""),
                "company": item.get("company_name", ""),
                "link": item.get("url", ""),
                "source": "Arbeitnow",
                "location": item.get("location", "Remote"),
                "description": item.get("description", "")[:MAX_JD_LENGTH],
            })

        logger.info("Arbeitnow: found {} jobs", len(jobs))
        return jobs
    except Exception as e:
        logger.error("Arbeitnow API failed: {}", e)
        return []


async def search_wellfound() -> list[dict]:
    try:
        url = "https://wellfound.com/jobs"
        try:
            html = await fetch_page(url)
        except Exception:
            from app.services.browser_service import get_page_content
            html = await get_page_content(url)
        listings = extract_job_listings(html)

        for listing in listings:
            listing["source"] = "Wellfound"
            listing["location"] = listing.get("location", "Remote")

        logger.info("Wellfound: found {} jobs", len(listings))
        return listings
    except Exception as e:
        logger.error("Wellfound scrape failed: {}", e)
        return []


async def search_jsearch() -> list[dict]:
    if not settings.RAPIDAPI_KEY:
        logger.warning("RapidAPI key not configured, skipping JSearch")
        return []
    try:
        headers = {
            "X-RapidAPI-Key": settings.RAPIDAPI_KEY,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
        }
        params = {
            "query": "software developer fresher India",
            "page": "1",
            "num_pages": "1",
            "date_posted": "week",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            res = await client.get(
                "https://jsearch.p.rapidapi.com/search",
                headers=headers,
                params=params,
            )
            res.raise_for_status()

        data = res.json()
        jobs = []

        for item in data.get("data", []):
            jobs.append({
                "title": item.get("job_title", ""),
                "company": item.get("employer_name", ""),
                "link": item.get("job_apply_link", ""),
                "source": "JSearch",
                "location": item.get("job_city", "India"),
                "description": item.get("job_description", "")[:MAX_JD_LENGTH],
            })

        logger.info("JSearch: found {} jobs", len(jobs))
        return jobs
    except Exception as e:
        logger.error("JSearch API failed: {}", e)
        return []


async def search_the_muse() -> list[dict]:
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                "https://www.themuse.com/api/public/jobs",
                params={"category": "Software Engineering", "level": "Entry Level", "page": 1},
            )
            response.raise_for_status()
            data = response.json()

        jobs = []
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)

        for item in data.get("results", []):
            try:
                pub_date = datetime.fromisoformat(item.get("publication_date", "").replace("Z", "+00:00"))
                if pub_date < cutoff:
                    continue
            except (ValueError, TypeError):
                pass

            company = item.get("company", {}).get("name", "Unknown")
            locs = item.get("locations", [])
            location = locs[0].get("name", "Remote") if locs else "Remote"

            jobs.append({
                "title": item.get("name", ""),
                "company": company,
                "link": item.get("refs", {}).get("landing_page", ""),
                "source": "TheMuse",
                "location": location,
                "description": item.get("contents", "")[:MAX_JD_LENGTH],
            })

        logger.info("TheMuse: found {} recent jobs", len(jobs))
        return jobs
    except Exception as e:
        logger.error("TheMuse API failed: {}", e)
        return []


async def fetch_job_description(url: str) -> str:
    if not url:
        return ""

    is_linkedin = "linkedin.com" in url

    try:
        html = await fetch_page(url)
        if is_linkedin:
            jd = extract_linkedin_jd(html)
            if jd:
                return jd[:MAX_JD_LENGTH]
        text = extract_text(html)
        if len(text) > 50:
            return text[:MAX_JD_LENGTH]
    except Exception:
        pass

    try:
        from app.services.browser_service import get_page_content
        html = await get_page_content(url)
        if is_linkedin:
            jd = extract_linkedin_jd(html)
            if jd:
                return jd[:MAX_JD_LENGTH]
        text = extract_text(html)
        if len(text) > 50:
            return text[:MAX_JD_LENGTH]
    except Exception as e:
        logger.error("Failed to fetch JD from {}: {}", url, e)

    return ""


async def discover_jobs(db: AsyncSession) -> list[dict]:
    from app.services.redis_service import is_job_seen, get_remaining_quota, store_raw_jobs

    remaining = get_remaining_quota()
    if remaining <= 0:
        logger.info("Daily job limit reached, skipping discovery")
        return []

    all_jobs = []

    api_sources = [
        search_remotive(),
        search_jobicy(),
        search_arbeitnow(),
        search_adzuna(),
        search_wellfound(),
        search_jsearch(),
        search_the_muse(),
    ]
    
    for q in SEARCH_QUERIES:
        api_sources.append(search_jobs_on_linkedin(q, max_days=1))

    import asyncio
    api_results = await asyncio.gather(*api_sources, return_exceptions=True)
    for result in api_results:
        if isinstance(result, list):
            all_jobs.extend(result)

    raw_stored = []
    for job_data in all_jobs:
        if len(raw_stored) >= remaining:
            logger.info("Reached remaining daily quota during discovery")
            break

        title = job_data.get("title", "")
        company = job_data.get("company", "Unknown")
        url = job_data.get("link", "")

        if _is_restricted_company(company):
            continue
        if not _is_relevant_role(title):
            continue
        if _is_senior_role(title):
            continue
        if not _is_recent(job_data.get("date", "")):
            continue
        if url and is_job_seen(url):
            continue

        raw_stored.append(job_data)

    if raw_stored:
        store_raw_jobs(raw_stored)
    
    logger.info("Discovered and queued {} raw jobs for cleaning", len(raw_stored))
    return raw_stored


async def clean_and_store_jobs(db: AsyncSession) -> list[dict]:
    from app.services.redis_service import get_raw_jobs, mark_job_seen
    from app.services.llm_service import invoke_llm
    from app.core.prompts import JOB_CLEAN_PROMPT
    import re
    import json

    raw_jobs = get_raw_jobs()
    if not raw_jobs:
        logger.info("No raw jobs to clean")
        return []

    cleaned_jobs = []
    
    for job_data in raw_jobs:
        url = job_data.get("link") or ""
        title = (job_data.get("title") or "").strip()
        company = (job_data.get("company") or "").strip() or "Unknown"
        location = (job_data.get("location") or "").strip() or "Remote"
        jd_text = (job_data.get("description") or "").strip()

        # Try fetching full description if API only provided a snippet
        if not jd_text or len(jd_text) < 150:
            fetched = await fetch_job_description(url)
            if fetched:
                jd_text = fetched

        # Rule-based cleaning (strip internal HTML if any)
        jd_text = re.sub(r'<[^>]+>', '', jd_text).strip()
        
        # Skip garbage
        if len(jd_text) < 50:
            continue
            
        jd_text = jd_text[:MAX_JD_LENGTH]

        # LLM cleaning only if core fields are broken/messy
        needs_llm = (
            len(title) < 3 or 
            len(title) > 100 or 
            "Unknown" in company or 
            len(company) > 100 or
            "\n" in title
        )

        if needs_llm:
            try:
                prompt_data = json.dumps({
                    "title": title,
                    "company": company,
                    "location": location,
                    "description": jd_text[:1000] # Give LLM enough context
                })
                prompt = JOB_CLEAN_PROMPT.format(raw_job=prompt_data)
                response = await invoke_llm(prompt, temperature=0.1)
                
                json_match = re.search(r"\{.*\}", response, re.DOTALL)
                if json_match:
                    clean_data = json.loads(json_match.group())
                    title = clean_data.get("title", title)[:500]
                    company = clean_data.get("company", company)[:300]
                    location = clean_data.get("location", location)[:300]
                    jd_text = clean_data.get("description", jd_text)[:MAX_JD_LENGTH]
            except Exception as e:
                logger.warning("LLM cleanup failed for {}, using raw values: {}", url, e)

        # Skip if title is still broken after cleanup
        if not title or len(title) < 3:
            continue

        job = Job(
            title=title,
            company=company,
            job_description=jd_text,
            source_url=url,
            location=location,
        )
        db.add(job)
        
        if url:
            mark_job_seen(url)
            
        cleaned_jobs.append({
            "title": title,
            "company": company,
            "url": url
        })

    await db.flush()
    logger.info("Cleaned and stored {} jobs into DB", len(cleaned_jobs))
    return cleaned_jobs
