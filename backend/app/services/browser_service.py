from loguru import logger
from playwright.async_api import async_playwright, Browser, Page


_browser: Browser | None = None


async def get_browser() -> Browser:
    global _browser
    if _browser and _browser.is_connected():
        return _browser

    pw = await async_playwright().start()
    _browser = await pw.chromium.launch(headless=True)
    logger.info("Browser launched")
    return _browser


async def close_browser():
    global _browser
    if _browser:
        await _browser.close()
        _browser = None
        logger.info("Browser closed")


async def get_page_content(url: str) -> str:
    browser = await get_browser()
    page = await browser.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_timeout(2000)
        return await page.content()
    finally:
        await page.close()


async def check_requires_login(url: str) -> bool:
    browser = await get_browser()
    page = await browser.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_timeout(2000)
        content = await page.content()
        login_indicators = [
            "sign in", "log in", "login", "create account",
            "sign up", "register", "password",
        ]
        text = content.lower()
        has_password = await page.query_selector("input[type='password']")

        if has_password:
            return True

        login_count = sum(1 for indicator in login_indicators if indicator in text)
        return login_count >= 3
    finally:
        await page.close()


async def attempt_form_fill(url: str, data: dict) -> bool:
    browser = await get_browser()
    page = await browser.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_timeout(2000)

        for field_name, value in data.items():
            selectors = [
                f"input[name='{field_name}']",
                f"input[placeholder*='{field_name}' i]",
                f"textarea[name='{field_name}']",
            ]
            for selector in selectors:
                element = await page.query_selector(selector)
                if element:
                    await element.fill(str(value))
                    break

        submit = await page.query_selector(
            "button[type='submit'], input[type='submit']"
        )
        if submit:
            try:
                await submit.click(timeout=5000)
                await page.wait_for_load_state("domcontentloaded", timeout=10000)
                logger.info("Form submitted on {}", url)
                return True
            except Exception as e:
                logger.warning("Found submit button but failed to click it on {}: {}", url, str(e).split('\n')[0])
                return False

        logger.warning("No submit button found on {}", url)
        return False
    except Exception as e:
        logger.error("Form fill failed on {}: {}", url, e)
        return False
    finally:
        await page.close()
