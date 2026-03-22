"""
데이터 수집 서비스
Naver, Yahoo Finance, StockTitan에서 최근 7일 뉴스/이슈를 수집합니다.
각 소스 실패 시에도 전체가 멈추지 않는 부분 실패 허용 구조입니다.
"""
import httpx
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.models.source_item import SourceItem
from app.models.weekly_run import WeeklyRun
from app.utils.logger import get_logger

logger = get_logger("collector")


async def collect_issues(db: AsyncSession, week_key: str) -> dict:
    """Run the full collection pipeline for the given week."""

    # Create or update weekly run
    run = WeeklyRun(
        week_key=week_key,
        status="running",
        run_started_at=datetime.now(),
    )
    db.add(run)
    await db.flush()

    results = {"naver": 0, "yahoo_finance": 0, "stocktitan": 0, "errors": []}

    # --- Naver News ---
    try:
        naver_items = await _collect_naver(week_key)
        for item in naver_items:
            db.add(item)
        results["naver"] = len(naver_items)
        logger.info(f"Naver: {len(naver_items)} items collected")
    except Exception as e:
        logger.error(f"Naver collection failed: {e}")
        results["errors"].append(f"naver: {str(e)}")

    # --- Yahoo Finance ---
    try:
        yahoo_items = await _collect_yahoo_finance(week_key)
        for item in yahoo_items:
            db.add(item)
        results["yahoo_finance"] = len(yahoo_items)
        logger.info(f"Yahoo Finance: {len(yahoo_items)} items collected")
    except Exception as e:
        logger.error(f"Yahoo Finance collection failed: {e}")
        results["errors"].append(f"yahoo_finance: {str(e)}")

    # --- StockTitan ---
    try:
        st_items = await _collect_stocktitan(week_key)
        for item in st_items:
            db.add(item)
        results["stocktitan"] = len(st_items)
        logger.info(f"StockTitan: {len(st_items)} items collected")
    except Exception as e:
        logger.error(f"StockTitan collection failed: {e}")
        results["errors"].append(f"stocktitan: {str(e)}")

    total = results["naver"] + results["yahoo_finance"] + results["stocktitan"]
    run.status = "completed" if total > 0 else "failed"
    run.run_finished_at = datetime.now()
    run.total_source_count = total
    run.note = "; ".join(results["errors"]) if results["errors"] else None

    await db.commit()
    return results


async def _collect_naver(week_key: str) -> list[SourceItem]:
    """Collect trending/economic news from Naver."""
    items = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    async with httpx.AsyncClient(timeout=30, headers=headers) as client:
        # Naver main page news section
        sections = ["경제", "증권", "산업"]
        for section in sections:
            try:
                url = f"https://search.naver.com/search.naver?where=news&query={section}+주요뉴스&sort=1&pd=4"
                resp = await client.get(url)
                if resp.status_code != 200:
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")
                news_items = soup.select(".news_tit")

                for news in news_items[:5]:
                    title = news.get_text(strip=True)
                    link = news.get("href", "")
                    if title:
                        items.append(SourceItem(
                            week_key=week_key,
                            source_type="news",
                            source_site="naver",
                            title=title,
                            url=link,
                            summary=f"네이버 {section} 섹션 뉴스",
                            published_at=datetime.now(),
                        ))
            except Exception as e:
                logger.warning(f"Naver section '{section}' failed: {e}")
                continue

    return items


async def _collect_yahoo_finance(week_key: str) -> list[SourceItem]:
    """Collect market news from Yahoo Finance."""
    items = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    async with httpx.AsyncClient(timeout=30, headers=headers) as client:
        try:
            resp = await client.get("https://finance.yahoo.com/news/", follow_redirects=True)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                headlines = soup.select("h3 a, [data-testid='story-title']")

                for h in headlines[:10]:
                    title = h.get_text(strip=True)
                    link = h.get("href", "")
                    if link and not link.startswith("http"):
                        link = f"https://finance.yahoo.com{link}"
                    if title and len(title) > 10:
                        items.append(SourceItem(
                            week_key=week_key,
                            source_type="news",
                            source_site="yahoo_finance",
                            title=title,
                            url=link,
                            summary="Yahoo Finance headline",
                            published_at=datetime.now(),
                        ))
        except Exception as e:
            logger.warning(f"Yahoo Finance main page failed: {e}")

    return items


async def _collect_stocktitan(week_key: str) -> list[SourceItem]:
    """Collect press releases from StockTitan."""
    items = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    async with httpx.AsyncClient(timeout=30, headers=headers) as client:
        try:
            resp = await client.get("https://www.stocktitan.net/press-releases/", follow_redirects=True)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                releases = soup.select("article a, .press-release-item a, [class*='release'] a")

                seen = set()
                for rel in releases[:15]:
                    title = rel.get_text(strip=True)
                    link = rel.get("href", "")
                    if title and len(title) > 10 and title not in seen:
                        seen.add(title)
                        if link and not link.startswith("http"):
                            link = f"https://www.stocktitan.net{link}"
                        items.append(SourceItem(
                            week_key=week_key,
                            source_type="filing",
                            source_site="stocktitan",
                            title=title,
                            url=link,
                            summary="StockTitan press release",
                            published_at=datetime.now(),
                        ))
        except Exception as e:
            logger.warning(f"StockTitan collection failed: {e}")

    return items
