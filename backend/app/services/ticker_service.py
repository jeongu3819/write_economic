"""
티커 분석 서비스
StockTitan (httpx + BeautifulSoup) 기반 데이터 수집 + OpenAI 트레이더 해석 생성.
"""
import json
import re
import time
from datetime import datetime
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from openai import AsyncOpenAI

from app.config import OPENAI_API_KEY, OPENAI_MODEL
from app.utils.logger import get_logger

logger = get_logger("ticker_service")

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9,ko;q=0.8",
}

# 간단한 인메모리 캐시 (1시간 TTL)
_cache: dict[str, dict] = {}
CACHE_TTL = 3600  # seconds


TRADER_ANALYSIS_PROMPT = """당신은 주식 시장 전문 트레이더입니다.
아래 제공되는 종목 정보(기업개요, 최신 뉴스 3개, 최신 공시 3개, 공매도 비율)를 분석하고,
트레이더 관점에서 해석을 제공해주세요.

## 규칙
1. 판단: "긍정", "부정", "중립" 중 하나를 선택
2. 해석: 2~4문장으로 간결하게 작성
3. 공시가 실질적 재료인지, 단순 정기/내부자 거래성 공시인지 구분
4. 과도하게 장황한 설명 금지
5. 한국어로 작성

## 출력 형식 (JSON)
{
  "sentiment": "긍정" | "부정" | "중립",
  "interpretation": "2~4문장의 해석"
}
"""

TRADER_SCHEMA = {
    "type": "object",
    "properties": {
        "sentiment": {"type": "string"},
        "interpretation": {"type": "string"},
    },
    "required": ["sentiment", "interpretation"],
    "additionalProperties": False,
}


async def analyze_ticker(ticker: str, model: Optional[str] = None) -> dict:
    """
    티커 분석 실행.
    1. StockTitan overview → 기업개요 + 공매도 비율
    2. StockTitan news → 최신 뉴스 3개
    3. StockTitan sec-filings → 최신 공시 3개
    4. OpenAI → 트레이더 해석
    """
    ticker = ticker.strip().upper()
    use_model = model or OPENAI_MODEL

    # 캐시 확인
    cache_key = f"{ticker}:{use_model}"
    if cache_key in _cache:
        cached = _cache[cache_key]
        if time.time() - cached["_cached_at"] < CACHE_TTL:
            logger.info(f"Cache hit for {ticker}")
            return cached["data"]

    result = {
        "ticker": ticker,
        "company_overview": "",
        "news": [],
        "filings": [],
        "short_interest": "데이터 없음",
        "short_interest_pct": None,
        "trader_sentiment": "중립",
        "trader_interpretation": "",
        "links": {
            "overview": f"https://www.stocktitan.net/overview/{ticker}/",
            "news": f"https://www.stocktitan.net/news/{ticker}/",
            "sec_filings": f"https://www.stocktitan.net/sec-filings/{ticker}/",
        },
        "model_used": use_model,
        "analyzed_at": datetime.now().isoformat(),
    }

    async with httpx.AsyncClient(timeout=30, headers=HEADERS, follow_redirects=True) as http:
        # 1. Overview
        try:
            overview_data = await _scrape_overview(http, ticker)
            result["company_overview"] = overview_data.get("overview", "")
            if overview_data.get("short_interest"):
                result["short_interest"] = overview_data["short_interest"]
            if overview_data.get("short_interest_pct"):
                result["short_interest_pct"] = overview_data["short_interest_pct"]
        except Exception as e:
            logger.warning(f"Overview scrape failed for {ticker}: {e}")

        # 2. News
        try:
            result["news"] = await _scrape_news(http, ticker)
        except Exception as e:
            logger.warning(f"News scrape failed for {ticker}: {e}")

        # 3. SEC Filings
        try:
            result["filings"] = await _scrape_filings(http, ticker)
        except Exception as e:
            logger.warning(f"Filings scrape failed for {ticker}: {e}")

    # 4. Trader interpretation via OpenAI
    try:
        trader_data = await _generate_trader_interpretation(result, use_model)
        result["trader_sentiment"] = trader_data.get("sentiment", "중립")
        result["trader_interpretation"] = trader_data.get("interpretation", "")
    except Exception as e:
        logger.warning(f"Trader interpretation failed for {ticker}: {e}")
        result["trader_interpretation"] = "AI 분석을 생성할 수 없습니다."

    # 캐시 저장
    _cache[cache_key] = {"data": result, "_cached_at": time.time()}

    return result


async def _scrape_overview(http: httpx.AsyncClient, ticker: str) -> dict:
    """StockTitan overview 페이지에서 기업개요 + 공매도 비율 추출."""
    url = f"https://www.stocktitan.net/overview/{ticker}/"
    resp = await http.get(url)
    data = {"overview": "", "short_interest": None, "short_interest_pct": None}

    if resp.status_code != 200:
        logger.warning(f"StockTitan overview returned {resp.status_code} for {ticker}")
        return data

    soup = BeautifulSoup(resp.text, "html.parser")

    # 기업개요: 보통 description 또는 about 섹션
    desc_el = (
        soup.select_one("meta[name='description']")
        or soup.select_one("meta[property='og:description']")
    )
    if desc_el:
        data["overview"] = desc_el.get("content", "").strip()

    # 페이지 본문에서 더 자세한 설명 찾기
    about_sections = soup.select("[class*='about'], [class*='description'], [class*='overview'], [class*='summary']")
    for section in about_sections:
        text = section.get_text(strip=True)
        if len(text) > len(data["overview"]):
            data["overview"] = text[:500]

    # 공매도(Short Interest) 추출
    text_content = soup.get_text()
    # "Short Interest" 패턴 찾기
    si_match = re.search(r"Short\s*Interest[:\s]*([0-9,.]+[MKB]?)", text_content, re.IGNORECASE)
    if si_match:
        data["short_interest"] = si_match.group(1).strip()

    # "% of Float" 패턴
    pct_match = re.search(r"(?:Short.*?)?(\d+\.?\d*)\s*%\s*(?:of\s*)?(?:Float|Outstanding)", text_content, re.IGNORECASE)
    if pct_match:
        data["short_interest_pct"] = f"{pct_match.group(1)}%"
        if not data["short_interest"] or data["short_interest"] is None:
            data["short_interest"] = f"{pct_match.group(1)}% of Float"

    return data


async def _scrape_news(http: httpx.AsyncClient, ticker: str) -> list[dict]:
    """StockTitan news 페이지에서 최신 뉴스 3개 추출."""
    url = f"https://www.stocktitan.net/news/{ticker}/"
    resp = await http.get(url)

    if resp.status_code != 200:
        logger.warning(f"StockTitan news returned {resp.status_code} for {ticker}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    items = []

    # 뉴스 항목 찾기 — 다양한 셀렉터 시도
    news_links = (
        soup.select("article a[href]")
        or soup.select("[class*='news'] a[href]")
        or soup.select("[class*='press'] a[href]")
        or soup.select("h2 a[href], h3 a[href]")
    )

    seen_titles = set()
    for link in news_links:
        title = link.get_text(strip=True)
        href = link.get("href", "")

        if not title or len(title) < 10 or title in seen_titles:
            continue
        seen_titles.add(title)

        if href and not href.startswith("http"):
            href = f"https://www.stocktitan.net{href}"

        # 날짜 추출 시도
        parent = link.find_parent(["article", "div", "li"])
        date_text = ""
        relative_time = ""
        if parent:
            time_el = parent.select_one("time, [datetime], [class*='date'], [class*='time']")
            if time_el:
                date_text = time_el.get("datetime", "") or time_el.get_text(strip=True)
                relative_time = time_el.get_text(strip=True)

        # 요약 추출 시도
        summary = ""
        if parent:
            desc_el = parent.select_one("p, [class*='desc'], [class*='summary'], [class*='snippet']")
            if desc_el:
                summary = desc_el.get_text(strip=True)[:150]

        items.append({
            "type": "뉴스",
            "title": title,
            "link": href,
            "date": date_text,
            "relative_time": relative_time or date_text,
            "summary": summary,
        })

        if len(items) >= 3:
            break

    return items


async def _scrape_filings(http: httpx.AsyncClient, ticker: str) -> list[dict]:
    """StockTitan sec-filings 페이지에서 최신 공시 3개 추출."""
    url = f"https://www.stocktitan.net/sec-filings/{ticker}/"
    resp = await http.get(url)

    if resp.status_code != 200:
        logger.warning(f"StockTitan filings returned {resp.status_code} for {ticker}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    items = []

    # 공시 항목 찾기
    filing_links = (
        soup.select("table a[href]")
        or soup.select("[class*='filing'] a[href]")
        or soup.select("article a[href]")
        or soup.select("h2 a[href], h3 a[href]")
    )

    seen_titles = set()
    for link in filing_links:
        title = link.get_text(strip=True)
        href = link.get("href", "")

        if not title or len(title) < 5 or title in seen_titles:
            continue
        # 네비게이션 링크 필터링
        if title.lower() in ("next", "previous", "home", "search", "back"):
            continue
        seen_titles.add(title)

        if href and not href.startswith("http"):
            href = f"https://www.stocktitan.net{href}"

        # 날짜 추출
        parent = link.find_parent(["tr", "article", "div", "li"])
        date_text = ""
        relative_time = ""
        if parent:
            time_el = parent.select_one("time, [datetime], td:nth-child(2), [class*='date']")
            if time_el:
                date_text = time_el.get("datetime", "") or time_el.get_text(strip=True)
                relative_time = time_el.get_text(strip=True)

        # 요약 추출
        summary = ""
        if parent:
            desc_el = parent.select_one("p, [class*='desc'], [class*='summary']")
            if desc_el:
                summary = desc_el.get_text(strip=True)[:150]

        items.append({
            "type": "공시",
            "title": title,
            "link": href,
            "date": date_text,
            "relative_time": relative_time or date_text,
            "summary": summary,
        })

        if len(items) >= 3:
            break

    return items


async def _generate_trader_interpretation(analysis: dict, model: str) -> dict:
    """OpenAI API로 트레이더 해석 생성."""
    # 분석 데이터 요약 생성
    news_text = "\n".join(
        [f"- {n['title']}" + (f": {n['summary']}" if n.get('summary') else "")
         for n in analysis.get("news", [])]
    ) or "뉴스 없음"

    filing_text = "\n".join(
        [f"- {f['title']}" + (f": {f['summary']}" if f.get('summary') else "")
         for f in analysis.get("filings", [])]
    ) or "공시 없음"

    user_prompt = f"""종목: {analysis['ticker']}
기업개요: {analysis.get('company_overview', '정보 없음')[:300]}

최신 뉴스:
{news_text}

최신 공시:
{filing_text}

공매도 비율: {analysis.get('short_interest', '데이터 없음')}

위 정보를 바탕으로 트레이더 관점의 해석을 제공해주세요."""

    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": TRADER_ANALYSIS_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "trader_interpretation",
                "schema": TRADER_SCHEMA,
                "strict": True,
            }
        },
    )

    output_text = response.choices[0].message.content
    return json.loads(output_text)
