"""
대기 / 딜레이 유틸리티
기존 server/utils/delay.js 의 Python 포팅
"""

import asyncio
import random


async def random_delay(min_ms: int = 1000, max_ms: int = 3000):
    """봇 탐지 회피를 위한 랜덤 딜레이"""
    delay_ms = random.randint(min_ms, max_ms)
    await asyncio.sleep(delay_ms / 1000)


async def human_type(page, selector: str, text: str):
    """사람처럼 한 글자씩 입력"""
    await page.click(selector)
    for char in text:
        await page.keyboard.type(char)
        await asyncio.sleep(random.uniform(0.05, 0.20))


async def wait_for_response_stable(
    page,
    container_selector: str,
    stable_seconds: int = 3,
    timeout_seconds: int = 120,
    min_length: int = 100,
) -> str:
    """
    ChatGPT 응답이 완전히 끝날 때까지 대기.
    - 텍스트가 min_length 이상이고
    - stable_seconds 동안 변화가 없으면 완료로 판정
    - timeout_seconds 초과 시 현재 텍스트 반환
    """
    import time

    start = time.time()
    last_text = ""
    stable_start: float | None = None

    while time.time() - start < timeout_seconds:
        try:
            containers = await page.query_selector_all(container_selector)
            if containers:
                last_container = containers[-1]
                current_text = (await last_container.text_content()) or ""
            else:
                current_text = ""
        except Exception:
            current_text = ""

        if current_text and len(current_text) >= min_length:
            if current_text == last_text:
                if stable_start is None:
                    stable_start = time.time()
                elif time.time() - stable_start >= stable_seconds:
                    return current_text
            else:
                stable_start = None
        last_text = current_text
        await asyncio.sleep(2)

    return last_text
