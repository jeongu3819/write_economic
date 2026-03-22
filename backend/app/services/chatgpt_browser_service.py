"""
ChatGPT 브라우저 자동화 서비스
기존 server/routes/analyze.js 의 Python/Playwright 포팅

Persistent context 기반으로 로그인 세션을 유지하며,
newstock GPT에 접속하여 프롬프트를 전송하고 응답을 추출한다.
"""

import asyncio
from datetime import datetime
from playwright.async_api import async_playwright, BrowserContext, Page

from app.core.config import settings, SELECTORS
from app.core.logger import log_manager
from app.utils.wait_helpers import random_delay, wait_for_response_stable
from app.utils.parser import clean_response_text, extract_plain_text


class ChatGPTError(Exception):
    """ChatGPT 자동화 관련 에러"""

    def __init__(self, message: str, error_type: str = "unknown"):
        super().__init__(message)
        self.error_type = error_type


async def run_chatgpt_query(ticker: str, scrape_data: dict | None = None) -> dict:
    """
    ChatGPT newstock GPT에 자동 질의하고 응답을 추출.

    Args:
        ticker: 종목 티커
        scrape_data: StockTitan 스크래핑 결과 (뉴스/공시)

    Returns:
        {
            "raw_response": str,
            "prompt_used": str,
        }
    """
    sel = SELECTORS["chatgpt"]
    context: BrowserContext | None = None

    try:
        await log_manager.broadcast("ChatGPT GPTs에 접속 중...", "info")

        async with async_playwright() as p:
            # ─── Persistent Context (세션 유지) ───
            context = await p.chromium.launch_persistent_context(
                settings.PLAYWRIGHT_USER_DATA_DIR,
                headless=settings.AUTOMATION_HEADLESS,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-blink-features=AutomationControlled"
                ],
                ignore_default_args=["--enable-automation"],
                user_agent=settings.USER_AGENT,
            )

            pages = context.pages
            page: Page = pages[0] if pages else await context.new_page()
            
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)

            # ─── Step 1: newstock GPT 접속 시도 ───
            accessed = await _try_direct_access(page, sel)
            if not accessed:
                accessed = await _try_sidebar_fallback(page, sel)

            if not accessed:
                raise ChatGPTError(
                    "newstock GPT에 접근할 수 없습니다. ChatGPT에 로그인되어 있는지 확인해주세요.",
                    "newstock_not_found",
                )

            # ─── Step 2: 로그인 확인 ───
            await _check_login(page, sel)

            # ─── Step 3: 프롬프트 생성 및 전송 ───
            prompt = _build_prompt(ticker, scrape_data)
            await _send_prompt(page, sel, prompt)

            # ─── Step 4: 응답 대기 및 추출 ───
            raw_response = await _extract_response(page, sel)

            if not raw_response or len(raw_response.strip()) < 50:
                raise ChatGPTError(
                    "AI 응답이 비어있거나 너무 짧습니다.", "empty_response"
                )

            await context.close()
            context = None

            await log_manager.broadcast(
                "AI 분석 완료! 응답을 추출했습니다.", "success"
            )

            return {
                "raw_response": raw_response,
                "prompt_used": prompt,
            }

    except ChatGPTError:
        raise
    except Exception as e:
        error_msg = str(e)
        error_type = "unknown"

        if "net::ERR" in error_msg or "Timeout" in error_msg.lower():
            error_type = "connection_failed"
            error_msg = f"ChatGPT 접속 실패: {error_msg}"
        elif "login" in error_msg.lower():
            error_type = "login_required"

        raise ChatGPTError(error_msg, error_type)
    finally:
        if context:
            await context.close()


# ───────────────────────────────────────────
# 내부 헬퍼 함수들
# ───────────────────────────────────────────


async def _try_direct_access(page: Page, sel: dict) -> bool:
    """1차: 직접 URL로 newstock GPT 접속 시도"""
    await log_manager.broadcast("newstock GPT 직접 URL로 접속 시도 중...", "info")
    try:
        await page.goto(
            settings.CHATGPT_GPT_URL,
            wait_until="domcontentloaded",
            timeout=60000,
        )
        await random_delay(3000, 5000)

        # 페이지가 ChatGPT 내부인지 확인 (입력창 존재 여부)
        textarea = await page.query_selector(sel["textArea"])
        if textarea:
            await log_manager.broadcast(
                "newstock GPT 직접 접속 성공!", "success"
            )
            return True

        # 로그인 페이지로 리디렉트 된 경우
        login_btn = await page.query_selector(sel["loginButton"])
        if login_btn:
            await log_manager.broadcast(
                "로그인이 필요합니다. 로그인 처리를 시도합니다...", "warn"
            )
            return False

        await log_manager.broadcast(
            "직접 URL 접속 결과가 불확실합니다. fallback 시도...", "warn"
        )
        return False

    except Exception as e:
        await log_manager.broadcast(
            f"직접 URL 접속 실패: {e}. fallback 시도...", "warn"
        )
        return False


async def _try_sidebar_fallback(page: Page, sel: dict) -> bool:
    """2차: chatgpt.com → 사이드바에서 newstock 탐색"""
    await log_manager.broadcast(
        "fallback: ChatGPT 메인 → 사이드바에서 newstock 탐색 중...", "info"
    )
    try:
        await page.goto(
            settings.CHATGPT_BASE_URL,
            wait_until="domcontentloaded",
            timeout=60000,
        )
        await random_delay(3000, 5000)

        # 로그인 확인
        login_btn = await page.query_selector(sel["loginButton"])
        if login_btn:
            await log_manager.broadcast(
                "로그인이 필요합니다. 브라우저에서 직접 로그인해주세요.", "error"
            )
            raise ChatGPTError(
                "ChatGPT 로그인이 필요합니다. playwright-session 디렉토리에서 "
                "먼저 수동 로그인을 완료해주세요.",
                "login_required",
            )

        # 사이드바에서 "newstock" 텍스트를 가진 요소 탐색
        # GPT 탐색 위에 있는 newstock을 찾아야 한다
        selectors_to_try = [
            'nav a:has-text("newstock")',
            'a:has-text("newstock")',
            'span:has-text("newstock")',
            'div[role="link"]:has-text("newstock")',
            'li:has-text("newstock")',
        ]

        for selector in selectors_to_try:
            try:
                el = await page.wait_for_selector(selector, timeout=5000)
                if el:
                    await el.click()
                    await random_delay(3000, 5000)

                    # 입력창이 나타났는지 확인
                    textarea = await page.query_selector(sel["textArea"])
                    if textarea:
                        await log_manager.broadcast(
                            "사이드바에서 newstock GPT 진입 성공!", "success"
                        )
                        return True
            except Exception:
                continue

        await log_manager.broadcast(
            "사이드바에서 newstock을 찾을 수 없습니다.", "error"
        )
        return False

    except ChatGPTError:
        raise
    except Exception as e:
        await log_manager.broadcast(f"사이드바 탐색 실패: {e}", "error")
        return False


async def _check_login(page: Page, sel: dict):
    """로그인 상태 확인 및 처리"""
    login_btn = await page.query_selector(sel["loginButton"])
    if login_btn:
        await log_manager.broadcast(
            "로그인 버튼 감지. 로그인을 시도합니다...", "info"
        )
        await login_btn.click()
        await random_delay(2000, 3000)

        # 구글 로그인 버튼 탐색
        try:
            google_btn = await page.wait_for_selector(
                sel["googleLoginButton"], timeout=15000
            )
            if google_btn:
                await log_manager.broadcast(
                    "구글로 계속하기 선택됨. 팝업된 브라우저에서 직접 계정을 선택해주세요.",
                    "info",
                )
                await google_btn.click()
                await random_delay(5000, 8000)
        except Exception:
            await log_manager.broadcast(
                "구글 로그인 버튼을 찾을 수 없습니다. 브라우저에서 직접 로그인해주세요.",
                "warn",
            )


def _build_prompt(ticker: str, scrape_data: dict | None = None) -> str:
    """newstock GPT용 프롬프트 생성 (StockTitan 데이터 포함)"""
    base_prompt = (
        f"{ticker} 기업개요, 최신뉴스 3개, 최신공시 3개, 공매도 비율, 트레이더 해석"
    )

    # StockTitan에서 수집한 뉴스가 있으면 프롬프트에 추가
    if scrape_data and scrape_data.get("news") and len(scrape_data["news"]) > 0:
        news_lines = []
        for n in scrape_data["news"][:5]:
            title = n.get("title", "")
            if title:
                news_lines.append(f"- {title}")

        if news_lines:
            news_context = "\n".join(news_lines)
            base_prompt += (
                f"\n\n참고: 오늘({scrape_data.get('date', '')}) StockTitan에서 "
                f"수집된 최신 뉴스/공시:\n{news_context}"
            )
    elif scrape_data and not scrape_data.get("has_news"):
        base_prompt += (
            f"\n\n참고: 오늘({scrape_data.get('date', '')}) StockTitan에서 "
            "새로운 뉴스/공시가 발견되지 않았습니다. 최근 동향 기반으로 분석해주세요."
        )

    return base_prompt


async def _send_prompt(page: Page, sel: dict, prompt: str):
    """프롬프트 입력 및 전송"""
    await log_manager.broadcast("입력창 대기 중...", "info")

    try:
        await page.wait_for_selector(sel["textArea"], timeout=120000)
    except Exception:
        raise ChatGPTError(
            "ChatGPT 입력창을 찾을 수 없습니다. 페이지가 제대로 로드되었는지 확인해주세요.",
            "textarea_not_found",
        )

    await random_delay(1000, 2000)

    await log_manager.broadcast("프롬프트를 입력 중...", "info")
    await page.fill(sel["textArea"], prompt)
    await random_delay(500, 1000)

    # 전송 버튼 클릭 또는 Enter
    await log_manager.broadcast("AI에게 분석을 요청 중...", "info")
    send_btn = await page.query_selector(sel["sendButton"])
    if send_btn:
        await send_btn.click()
    else:
        await page.keyboard.press("Enter")


async def _extract_response(page: Page, sel: dict) -> str:
    """응답 완료까지 대기하고 마지막 assistant 응답 추출"""
    await log_manager.broadcast(
        f"AI 응답 대기 중... (최대 {settings.REQUEST_TIMEOUT // 1000}초)", "info"
    )

    # 응답 컨테이너가 나타날 때까지 대기
    try:
        await page.wait_for_selector(
            sel["responseContainer"], timeout=settings.REQUEST_TIMEOUT
        )
    except Exception:
        raise ChatGPTError(
            "AI 응답을 기다리는 중 타임아웃이 발생했습니다.", "response_timeout"
        )

    await random_delay(5000, 8000)

    # 응답이 완전히 완료될 때까지 대기
    await log_manager.broadcast("응답 생성 완료 대기 중...", "info")
    _ = await wait_for_response_stable(
        page,
        sel["responseContainer"],
        stable_seconds=settings.RESPONSE_STABLE_SECONDS,
        timeout_seconds=settings.REQUEST_TIMEOUT // 1000,
    )

    # 마지막 assistant 응답에서 HTML 콘텐츠 추출
    response_html = await page.evaluate(
        """(selectors) => {
            const containers = document.querySelectorAll(selectors.container);
            if (containers.length === 0) return '';
            const last = containers[containers.length - 1];
            const markdown = last.querySelector(selectors.text);
            return markdown ? markdown.innerHTML : last.innerHTML;
        }""",
        {
            "container": sel["responseContainer"],
            "text": sel["responseText"],
        },
    )

    if not response_html:
        # Fallback: 텍스트로 추출
        try:
            containers = await page.query_selector_all(sel["responseContainer"])
            if containers:
                response_html = await containers[-1].inner_html()
        except Exception:
            pass

    return clean_response_text(response_html or "")


# ───────────────────────────────────────────
# 세션 확인 유틸리티
# ───────────────────────────────────────────


async def check_session() -> dict:
    """
    ChatGPT 세션 상태 확인.
    접속 가능 여부, 로그인 상태, newstock 접근 가능 여부를 점검.
    """
    sel = SELECTORS["chatgpt"]
    result = {
        "chatgpt_accessible": False,
        "logged_in": False,
        "newstock_direct_access": False,
        "newstock_sidebar_access": False,
        "message": "",
    }

    context: BrowserContext | None = None

    try:
        async with async_playwright() as p:
            context = await p.chromium.launch_persistent_context(
                settings.PLAYWRIGHT_USER_DATA_DIR,
                headless=settings.AUTOMATION_HEADLESS,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-blink-features=AutomationControlled"
                ],
                ignore_default_args=["--enable-automation"],
                user_agent=settings.USER_AGENT,
            )

            pages = context.pages
            page: Page = pages[0] if pages else await context.new_page()
            
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)

            # 1) ChatGPT 접속 확인
            try:
                await page.goto(
                    settings.CHATGPT_BASE_URL,
                    wait_until="domcontentloaded",
                    timeout=30000,
                )
                await random_delay(2000, 3000)
                result["chatgpt_accessible"] = True
            except Exception:
                result["message"] = "ChatGPT에 접속할 수 없습니다."
                return result

            # 2) 로그인 확인
            login_btn = await page.query_selector(sel["loginButton"])
            if login_btn:
                result["message"] = "로그인이 필요합니다."
                return result
            result["logged_in"] = True

            # 3) newstock 직접 URL 확인
            try:
                await page.goto(
                    settings.CHATGPT_GPT_URL,
                    wait_until="domcontentloaded",
                    timeout=30000,
                )
                await random_delay(2000, 3000)
                textarea = await page.query_selector(sel["textArea"])
                if textarea:
                    result["newstock_direct_access"] = True
            except Exception:
                pass

            # 4) 사이드바 확인 (간단)
            if not result["newstock_direct_access"]:
                try:
                    await page.goto(
                        settings.CHATGPT_BASE_URL,
                        wait_until="domcontentloaded",
                        timeout=30000,
                    )
                    await random_delay(2000, 3000)
                    el = await page.query_selector(
                        'a:has-text("newstock"), span:has-text("newstock")'
                    )
                    result["newstock_sidebar_access"] = el is not None
                except Exception:
                    pass

            # 결과 메시지
            if result["newstock_direct_access"]:
                result["message"] = "ready"
            elif result["newstock_sidebar_access"]:
                result["message"] = "ready (sidebar fallback)"
            else:
                result["message"] = (
                    "ChatGPT에 로그인은 되어 있지만 newstock GPT를 찾을 수 없습니다."
                )

            await context.close()
            context = None

    except Exception as e:
        result["message"] = f"세션 확인 오류: {e}"
    finally:
        if context:
            await context.close()

    return result
