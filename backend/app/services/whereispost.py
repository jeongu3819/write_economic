"""
whereispost.com 키워드 데이터 조회 서비스
검색량, 문서 수, 비율 등을 가져옵니다.
"""
import httpx
from bs4 import BeautifulSoup
from app.utils.logger import get_logger

logger = get_logger("whereispost")


async def fetch_keyword_metrics(keyword: str) -> dict:
    """Fetch search volume, document count, ratio from whereispost.com."""
    result = {
        "search_volume": 0,
        "document_count": 0,
        "keyword_ratio": 0.0,
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://whereispost.com/keyword/",
    }

    try:
        async with httpx.AsyncClient(timeout=15, headers=headers) as client:
            # whereispost keyword search
            resp = await client.get(
                f"https://whereispost.com/keyword/",
                params={"query": keyword},
                follow_redirects=True,
            )

            if resp.status_code != 200:
                logger.warning(f"whereispost returned {resp.status_code} for '{keyword}'")
                return result

            soup = BeautifulSoup(resp.text, "html.parser")

            # Try to parse metrics from the page
            # The exact selectors depend on the page structure
            tables = soup.select("table")
            for table in tables:
                rows = table.select("tr")
                for row in rows:
                    cells = row.select("td, th")
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True).lower()
                        value_text = cells[1].get_text(strip=True).replace(",", "")

                        if "검색량" in label or "search" in label:
                            try:
                                result["search_volume"] = int(value_text)
                            except ValueError:
                                pass
                        elif "문서" in label or "document" in label:
                            try:
                                result["document_count"] = int(value_text)
                            except ValueError:
                                pass
                        elif "비율" in label or "ratio" in label:
                            try:
                                result["keyword_ratio"] = float(value_text.replace("%", ""))
                            except ValueError:
                                pass

            # Fallback: try to find numbers in specific elements
            if result["search_volume"] == 0:
                numbers = soup.select(".result-number, .metric-value, [class*='volume']")
                for i, num_el in enumerate(numbers[:3]):
                    val_text = num_el.get_text(strip=True).replace(",", "")
                    try:
                        val = int(val_text)
                        if i == 0:
                            result["search_volume"] = val
                        elif i == 1:
                            result["document_count"] = val
                    except ValueError:
                        pass

    except Exception as e:
        logger.warning(f"whereispost fetch failed for '{keyword}': {e}")

    if result["search_volume"] > 0 and result["document_count"] > 0:
        result["keyword_ratio"] = round(
            result["search_volume"] / result["document_count"], 4
        )

    return result
