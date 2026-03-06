import httpx
from bs4 import BeautifulSoup
from loguru import logger


async def fetch_page(url: str) -> str:
    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=30.0,
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        },
    ) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.text


def extract_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)


def extract_linkedin_jd(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")

    jd_selectors = [
        ".show-more-less-html__markup",
        ".description__text",
        "div.description",
        "section.description",
        ".jobs-description__content",
        "div[class*='description']",
    ]

    for selector in jd_selectors:
        el = soup.select_one(selector)
        if el:
            for tag in el(["script", "style"]):
                tag.decompose()
            text = el.get_text(separator="\n", strip=True)
            if len(text) > 50:
                return text[:5000]

    article = soup.select_one("article") or soup.select_one("main")
    if article:
        for tag in article(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        for similar in article.select(".similar-jobs, .jobs-similar, [class*='similar']"):
            similar.decompose()
        text = article.get_text(separator="\n", strip=True)
        if len(text) > 50:
            return text[:5000]

    return ""


def extract_job_listings(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    listings = []

    selectors = [
        {"container": ".base-card", "title": ".base-search-card__title", "company": ".base-search-card__subtitle", "link": "a.base-card__full-link", "date": "time"},
        {"container": "div.job-card", "title": "h3", "company": ".company-name", "link": "a", "date": "time"},
        {"container": "li.job-listing", "title": "h2", "company": ".company", "link": "a", "date": "time"},
    ]

    for selector in selectors:
        cards = soup.select(selector["container"])
        if not cards:
            continue

        for card in cards:
            title_el = card.select_one(selector["title"])
            company_el = card.select_one(selector["company"])
            link_el = card.select_one(selector["link"])
            date_el = card.select_one(selector.get("date", "time"))

            if title_el:
                listing = {
                    "title": title_el.get_text(strip=True),
                    "company": company_el.get_text(strip=True) if company_el else "Unknown",
                    "link": link_el.get("href", "") if link_el else "",
                    "date": date_el.get("datetime", "") if date_el else "",
                }
                listings.append(listing)

        if listings:
            break

    logger.info("Extracted {} job listings", len(listings))
    return listings
