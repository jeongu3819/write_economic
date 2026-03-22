"""
Pydantic 스키마 — 요청/응답 모델
"""

from pydantic import BaseModel, Field
from typing import Optional


class GenerateRequest(BaseModel):
    """POST /api/stock/generate 요청"""
    ticker: str = Field(..., min_length=1, max_length=10, description="종목 티커 (예: AMD, AAPL)")


class ScrapeResult(BaseModel):
    """StockTitan 스크래핑 결과"""
    ticker: str
    date: str
    has_news: bool
    news_count: int
    news: list[dict] = []
    all_news: list[dict] = []


class GenerateResponse(BaseModel):
    """POST /api/stock/generate 응답"""
    ticker: str
    prompt_used: str
    raw_response: str
    blog_title: str
    blog_content: str
    sections: dict = {}
    scrape_data: Optional[ScrapeResult] = None


class SessionStatus(BaseModel):
    """GET /api/stock/check-session 응답"""
    chatgpt_accessible: bool = False
    logged_in: bool = False
    newstock_direct_access: bool = False
    newstock_sidebar_access: bool = False
    message: str = ""


class ErrorResponse(BaseModel):
    """에러 응답"""
    error: str
    error_type: str = "unknown"
    detail: Optional[str] = None
