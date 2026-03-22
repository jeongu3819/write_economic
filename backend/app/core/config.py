"""
환경 설정 및 CSS 셀렉터 관리
기존 server/config/selectors.config.js + .env 설정을 통합
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")


class Settings:
    """애플리케이션 설정"""

    # 서버 설정
    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", "8000"))
    FRONTEND_PORT: int = int(os.getenv("FRONTEND_PORT", "3000"))

    # Playwright 설정
    PLAYWRIGHT_USER_DATA_DIR: str = os.getenv(
        "PLAYWRIGHT_USER_DATA_DIR",
        str(Path(__file__).resolve().parent.parent.parent / "playwright-session"),
    )
    AUTOMATION_HEADLESS: bool = os.getenv("AUTOMATION_HEADLESS", "false").lower() == "true"

    # ChatGPT URL
    CHATGPT_BASE_URL: str = os.getenv("CHATGPT_BASE_URL", "https://chatgpt.com/")
    CHATGPT_GPT_URL: str = os.getenv(
        "CHATGPT_GPT_URL",
        "https://chatgpt.com/g/g-67f26f292d908191af9814f781eff794-newstock",
    )

    # StockTitan
    STOCKTITAN_BASE_URL: str = os.getenv(
        "STOCKTITAN_BASE_URL", "https://stocktitan.net"
    )

    # 타임아웃
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "120000"))  # ms
    RESPONSE_STABLE_SECONDS: int = int(os.getenv("RESPONSE_STABLE_SECONDS", "3"))

    # 사용자 에이전트
    USER_AGENT: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )


settings = Settings()


# ───────────────────────────────────────────
# CSS 셀렉터 중앙 관리 (기존 selectors.config.js 포팅)
# ───────────────────────────────────────────

SELECTORS = {
    "stocktitan": {
        "newsItem": "article, .news-item, .press-release-item, [class*='release']",
        "newsDate": "time, .date, [class*='date'], [datetime]",
        "newsTitle": "h2 a, h3 a, .title a, [class*='title'] a",
        "newsLink": "a[href*='press-release'], a[href*='news']",
    },
    "chatgpt": {
        "loginButton": '[data-testid="login-button"]',
        "googleLoginButton": 'button[data-provider="google"]',
        "textArea": '#prompt-textarea, textarea[data-id="root"]',
        "sendButton": 'button[data-testid="send-button"], button[aria-label="Send prompt"]',
        "responseContainer": '[data-message-author-role="assistant"]',
        "responseText": '.markdown, .prose, [class*="markdown"]',
        "stopButton": 'button[data-testid="stop-button"], button[aria-label="Stop generating"]',
    },
}
