"""
주간 뉴스/이슈 수집 서비스
- Naver News section/104 (세계 뉴스)
- Yahoo Finance
소스를 리스트로 관리하여 나중에 경제/IT 섹션 쉽게 추가 가능.
각 소스 실패 시에도 전체가 멈추지 않는 부분 실패 허용 구조.
"""
import httpx
from bs4 import BeautifulSoup
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.source_item import SourceItem
from app.models.weekly_run import WeeklyRun
from app.utils.logger import get_logger
from app.utils.week import get_week_date_range

logger = get_logger("collector")

# ── 확장 가능한 소스 설정 ──
# 네이버 뉴스 섹션 목록 (나중에 경제=101, IT=105 등 추가 가능)
NAVER_SECTIONS = [
    {"id": "104", "name": "세계", "source_type": "news"},
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}


async def collect_issues(db: AsyncSession, week_key: str) -> dict:
    """Run the full collection pipeline for the given week."""
    run = WeeklyRun(
        week_key=week_key,
        status="running",
        run_started_at=datetime.now(),
    )
    db.add(run)
    await db.flush()

    # 중복 URL 체크용
    existing = await db.execute(
        select(SourceItem.url).where(SourceItem.week_key == week_key)
    )
    existing_urls = {row[0] for row in existing.all() if row[0]}

    results = {"naver": 0, "yahoo_finance": 0, "errors": []}

    # --- Naver News ---
    try:
        naver_items = await _collect_naver(week_key, existing_urls)
        for item in naver_items:
            db.add(item)
            existing_urls.add(item.url)
        results["naver"] = len(naver_items)
        logger.info(f"Naver: {len(naver_items)} items collected")
    except Exception as e:
        logger.error(f"Naver collection failed: {e}")
        results["errors"].append(f"naver: {str(e)}")

    # --- Yahoo Finance ---
    try:
        yahoo_items = await _collect_yahoo_finance(week_key, existing_urls)
        for item in yahoo_items:
            db.add(item)
            existing_urls.add(item.url)
        results["yahoo_finance"] = len(yahoo_items)
        logger.info(f"Yahoo Finance: {len(yahoo_items)} items collected")
    except Exception as e:
        logger.error(f"Yahoo Finance collection failed: {e}")
        results["errors"].append(f"yahoo_finance: {str(e)}")

    total = results["naver"] + results["yahoo_finance"]
    run.status = "completed" if total > 0 else "failed"
    run.run_finished_at = datetime.now()
    run.total_source_count = total
    run.note = "; ".join(results["errors"]) if results["errors"] else None

    await db.commit()
    return results


async def _collect_naver(week_key: str, existing_urls: set) -> list[SourceItem]:
    """Collect news from Naver News section pages."""
    items = []

    async with httpx.AsyncClient(timeout=30, headers=HEADERS, follow_redirects=True) as client:
        for section in NAVER_SECTIONS:
            try:
                url = f"https://news.naver.com/section/{section['id']}"
                resp = await client.get(url)
                if resp.status_code != 200:
                    logger.warning(f"Naver section {section['id']} returned {resp.status_code}")
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")

                # 네이버 뉴스 섹션 페이지의 기사 링크 추출
                # 헤드라인 뉴스
                headlines = soup.select("a.sa_text_title")

                for news in headlines[:15]:
                    title = news.get_text(strip=True)
                    link = news.get("href", "")

                    if not title or len(title) < 5:
                        continue
                    if link in existing_urls:
                        continue

                    items.append(SourceItem(
                        week_key=week_key,
                        source_type=section["source_type"],
                        source_site="naver",
                        title=title,
                        url=link,
                        summary=f"네이버 {section['name']} 섹션 뉴스",
                        published_at=datetime.now(),
                    ))

            except Exception as e:
                logger.warning(f"Naver section '{section['name']}' failed: {e}")
                continue

    return items


async def _collect_yahoo_finance(week_key: str, existing_urls: set) -> list[SourceItem]:
    """Collect market news from Yahoo Finance Latest News."""
    items = []

    async with httpx.AsyncClient(timeout=30, headers=HEADERS, follow_redirects=True) as client:
        try:
            resp = await client.get("https://finance.yahoo.com/topic/latest-news/")
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")

                # Yahoo Finance 최신 뉴스 페이지 헤드라인
                headlines = (
                    soup.select("h3 a")
                    or soup.select("[data-testid='story-title']")
                    or soup.select("a.js-content-viewer")
                    or soup.select("a[href*='/news/']")
                )

                for h in headlines[:20]:
                    title = h.get_text(strip=True)
                    link = h.get("href", "")

                    if link and not link.startswith("http"):
                        link = f"https://finance.yahoo.com{link}"

                    if not title or len(title) < 10:
                        continue
                    if link in existing_urls:
                        continue

                    items.append(SourceItem(
                        week_key=week_key,
                        source_type="news",
                        source_site="yahoo_finance",
                        title=title,
                        url=link,
                        summary="Yahoo Finance Latest News",
                        published_at=datetime.now(),
                    ))
        except Exception as e:
            logger.warning(f"Yahoo Finance latest news failed: {e}")

    return items
