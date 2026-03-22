"""
주식 분석 API 라우트
POST /api/stock/generate   - 티커 분석 + 블로그 생성
GET  /api/stock/check-session - 세션 상태 확인
"""

from fastapi import APIRouter, HTTPException

from app.schemas.stock import (
    GenerateRequest,
    GenerateResponse,
    SessionStatus,
    ErrorResponse,
    ScrapeResult,
)
from app.services.stocktitan_scraper_service import scrape_stocktitan
from app.services.chatgpt_browser_service import (
    run_chatgpt_query,
    check_session,
    ChatGPTError,
)
from app.services.blog_writer_service import generate_blog
from app.core.logger import log_manager

router = APIRouter(prefix="/api/stock", tags=["stock"])


@router.post("/generate", response_model=GenerateResponse)
async def generate_stock_blog(req: GenerateRequest):
    """
    티커 입력 → StockTitan 스크래핑 → newstock GPT 자동 질의 → 블로그 생성
    """
    ticker = req.ticker.strip().upper()

    if not ticker or len(ticker) > 10:
        raise HTTPException(status_code=400, detail="유효하지 않은 티커입니다.")

    await log_manager.broadcast(
        f'[시작] 티커 "{ticker}" 분석을 시작합니다...', "system"
    )

    # ── Step 1: StockTitan 스크래핑 ──
    await log_manager.broadcast(
        "[Step 1] StockTitan 데이터 수집 중...", "info"
    )
    scrape_data = await scrape_stocktitan(ticker)
    await log_manager.broadcast(
        f"[Step 1 완료] 뉴스 {scrape_data.get('news_count', 0)}건 수집", "success"
    )

    # ── Step 2: newstock GPT 자동 질의 ──
    await log_manager.broadcast(
        "[Step 2] newstock GPT 분석 중...", "info"
    )
    try:
        gpt_result = await run_chatgpt_query(ticker, scrape_data)
    except ChatGPTError as e:
        await log_manager.broadcast(f"[에러] {e}", "error")
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "error_type": e.error_type,
            },
        )

    await log_manager.broadcast("[Step 2 완료] AI 응답 추출 성공", "success")

    # ── Step 3: 블로그 생성 ──
    await log_manager.broadcast("[Step 3] 블로그 글 생성 중...", "info")
    blog_result = generate_blog(ticker, gpt_result["raw_response"])
    await log_manager.broadcast("[Step 3 완료] 블로그 원고가 생성되었습니다!", "success")

    return GenerateResponse(
        ticker=ticker,
        prompt_used=gpt_result["prompt_used"],
        raw_response=gpt_result["raw_response"],
        blog_title=blog_result["blog_title"],
        blog_content=blog_result["blog_content"],
        sections=blog_result["sections"],
        scrape_data=ScrapeResult(**scrape_data),
    )


@router.get("/check-session", response_model=SessionStatus)
async def check_chatgpt_session():
    """ChatGPT 세션 상태 확인"""
    await log_manager.broadcast("세션 상태 확인 중...", "info")
    result = await check_session()
    return SessionStatus(**result)
