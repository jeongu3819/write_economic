"""
Pydantic 스키마 — 티커 분석 요청/응답 모델
"""
from pydantic import BaseModel, Field
from typing import Optional


class TickerAnalyzeRequest(BaseModel):
    """POST /api/ticker/analyze 요청"""
    ticker: str = Field(..., min_length=1, max_length=10, description="종목 티커 (예: NVDA, AAPL)")
    model: Optional[str] = Field(None, description="사용할 OpenAI 모델 (미지정 시 기본 모델)")


class NewsItem(BaseModel):
    """뉴스/공시 항목"""
    type: str = "뉴스"
    title: str = ""
    link: str = ""
    date: str = ""
    relative_time: str = ""
    summary: str = ""


class TickerAnalyzeResponse(BaseModel):
    """POST /api/ticker/analyze 응답"""
    ticker: str
    company_overview: str = ""
    news: list[NewsItem] = []
    filings: list[NewsItem] = []
    short_interest: str = "데이터 없음"
    short_interest_pct: Optional[str] = None
    trader_sentiment: str = "중립"
    trader_interpretation: str = ""
    links: dict = {}
    model_used: str = ""
    analyzed_at: str = ""


class TickerBlogifyRequest(BaseModel):
    """POST /api/ticker/blogify 요청"""
    ticker: str = Field(..., min_length=1, max_length=10)
    analysis_data: dict = Field(..., description="analyze 응답 결과 전체")
    platform: str = Field("naver", description="naver 또는 tistory")
    model: Optional[str] = None


class TickerBlogifyResponse(BaseModel):
    """POST /api/ticker/blogify 응답"""
    ticker: str
    titles: list[str] = []
    intros: list[str] = []
    body: str = ""
    summary: str = ""
    hashtags: list[str] = []
    caution: str = ""
    platform: str = "naver"


class ModelInfo(BaseModel):
    """모델 정보"""
    id: str
    owned_by: str = ""


class ModelsResponse(BaseModel):
    """GET /api/models 응답"""
    models: list[ModelInfo] = []
    default_model: str = ""
