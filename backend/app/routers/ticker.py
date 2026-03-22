"""Ticker analysis router."""
from fastapi import APIRouter

from app.schemas.ticker import (
    TickerAnalyzeRequest,
    TickerAnalyzeResponse,
    TickerBlogifyRequest,
    TickerBlogifyResponse,
)
from app.services.ticker_service import analyze_ticker
from app.services.ticker_blogify_service import blogify_ticker
from app.utils.response import api_response

router = APIRouter(prefix="/api/ticker", tags=["ticker"])


@router.post("/analyze")
async def analyze(body: TickerAnalyzeRequest):
    """
    티커 분석 실행.
    StockTitan에서 기업개요, 최신 뉴스 3개, 최신 공시 3개, 공매도 비율을 수집하고
    OpenAI로 트레이더 해석을 생성합니다.
    """
    try:
        result = await analyze_ticker(body.ticker, body.model)
        return api_response(data=result)
    except Exception as e:
        return api_response(success=False, error=f"분석 실패: {str(e)}")


@router.post("/blogify")
async def blogify(body: TickerBlogifyRequest):
    """
    티커 분석 결과를 블로그 형식으로 변환합니다.
    """
    try:
        result = await blogify_ticker(
            analysis_data=body.analysis_data,
            platform=body.platform,
            model=body.model,
        )
        return api_response(data=result)
    except Exception as e:
        return api_response(success=False, error=f"블로그 변환 실패: {str(e)}")
