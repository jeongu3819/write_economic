"""
StockTitan 스크래핑 서비스
기존 server/routes/scrape.js 의 Python/Playwright 포팅

StockTitan은 오늘 나온 뉴스/공시를 가장 빠르게 올려주는 소스.
이 데이터를 먼저 수집한 뒤 newstock GPT 프롬프트에 포함시킨다.
"""

from datetime import datetime
from playwright.async_api import async_playwright, Browser, BrowserContext

from app.core.config import settings, SELECTORS
from app.core.logger import log_manager
from app.utils.wait_helpers import random_delay


async def scrape_stocktitan(ticker: str) -> dict:
    """
    StockTitan에서 티커 관련 뉴스/공시를 스크래핑.

    Returns:
        {
            "ticker": str,
            "date": str,
            "has_news": bool,
            "news_count": int,
            "news": [{"title": str, "link": str, "date": str}, ...],
            "all_news": [...]
        }
    """
    browser: Browser | None = None
    sel = SELECTORS["stocktitan"]

    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")

    await log_manager.broadcast(
        f'StockTitan에서 "{ticker}" 검색을 시작합니다...', "info"
    )

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,  # StockTitan은 headless로 충분
                args=["--no-sandbox", "--disable-setuid-sandbox"],
            )
            context = await browser.new_context(user_agent=settings.USER_AGENT)
            page = await context.new_page()

            # StockTitan 검색 페이지로 이동
            await log_manager.broadcast("StockTitan 사이트에 접속 중...", "info")
            search_url = f"{settings.STOCKTITAN_BASE_URL}/search?q={ticker}"
            await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            await random_delay(2000, 4000)

            await log_manager.broadcast(
                f"오늘 날짜({today_str}) 뉴스/공시를 검색 중...", "info"
            )

            # 뉴스 항목 추출
            news_items = await page.evaluate(
                """(selector) => {
                    const items = document.querySelectorAll(selector);
                    return Array.from(items).slice(0, 20).map(item => {
                        const titleEl = item.querySelector('h2 a, h3 a, [class*="title"] a, a');
                        const dateEl = item.querySelector('time, [class*="date"], [datetime]');
                        return {
                            title: titleEl?.textContent?.trim() || '',
                            link: titleEl?.href || '',
                            date: dateEl?.getAttribute('datetime') || dateEl?.textContent?.trim() || ''
                        };
                    }).filter(item => item.title);
                }""",
                sel["newsItem"],
            )

            # 오늘 날짜 뉴스 필터링
            todays_news = [
                item for item in news_items
                if item.get("date") and today_str in item["date"]
            ]

            await browser.close()
            browser = None

            if todays_news:
                await log_manager.broadcast(
                    f"오늘의 뉴스 {len(todays_news)}건 발견!", "success"
                )
                return {
                    "ticker": ticker,
                    "date": today_str,
                    "has_news": True,
                    "news_count": len(todays_news),
                    "news": todays_news,
                    "all_news": news_items[:10],
                }
            else:
                await log_manager.broadcast(
                    f"오늘의 뉴스는 없습니다. 최근 뉴스 {len(news_items)}건을 반환합니다.",
                    "warn",
                )
                return {
                    "ticker": ticker,
                    "date": today_str,
                    "has_news": False,
                    "news_count": 0,
                    "news": [],
                    "all_news": news_items[:10],
                }

    except Exception as e:
        await log_manager.broadcast(f"StockTitan 스크래핑 오류: {e}", "error")
        # 스크래핑 실패해도 전체 흐름은 계속 진행 (GPT만으로도 가능)
        return {
            "ticker": ticker,
            "date": today_str,
            "has_news": False,
            "news_count": 0,
            "news": [],
            "all_news": [],
        }
    finally:
        if browser:
            await browser.close()
