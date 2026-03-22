"""
ChatGPT 응답 파싱 유틸리티
"""

import re
from typing import Optional


def clean_response_text(raw_html: str) -> str:
    """ChatGPT 응답 HTML에서 불필요한 UI 텍스트 제거"""
    if not raw_html:
        return ""

    # 복사 버튼, 메뉴 텍스트 등 제거
    text = re.sub(r"Copy code", "", raw_html)
    text = re.sub(r"<button[^>]*>.*?</button>", "", text, flags=re.DOTALL)
    # 연속 공백 정리 (줄바꿈은 유지)
    text = re.sub(r"[ \t]+", " ", text)
    # 빈 줄 3개 이상 → 2개로
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_plain_text(html: str) -> str:
    """HTML 태그를 제거하고 순수 텍스트만 추출"""
    if not html:
        return ""
    text = re.sub(r"<br\s*/?>", "\n", html)
    text = re.sub(r"</?p[^>]*>", "\n", text)
    text = re.sub(r"</?li[^>]*>", "\n• ", text)
    text = re.sub(r"</?h[1-6][^>]*>", "\n\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&#39;", "'", text)
    text = re.sub(r"&quot;", '"', text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def parse_sections(text: str) -> dict:
    """
    ChatGPT 응답 텍스트를 섹션별로 파싱.
    키워드 기반으로 기업개요 / 뉴스 / 공시 / 공매도 / 트레이더 해석을 분리.
    """
    sections = {
        "company_overview": "",
        "news_summary": [],
        "filings_summary": [],
        "short_interest": "",
        "trader_view": "",
    }

    if not text:
        return sections

    # 키워드 패턴 (유연하게 매칭)
    patterns = {
        "company_overview": r"(?:기업\s*개요|company\s*overview|기업\s*소개)",
        "news": r"(?:최신\s*뉴스|뉴스\s*요약|news|주요\s*뉴스)",
        "filings": r"(?:최신\s*공시|공시\s*요약|filings|SEC\s*공시|최근\s*공시)",
        "short": r"(?:공매도\s*비율|short\s*interest|공매도)",
        "trader": r"(?:트레이더\s*해석|트레이더\s*관점|trader|투자\s*관점|단기\s*트레이더)",
    }

    lines = text.split("\n")
    current_section: Optional[str] = None
    current_lines: list[str] = []

    def _flush():
        nonlocal current_section, current_lines
        if not current_section or not current_lines:
            current_lines = []
            return
        content = "\n".join(current_lines).strip()
        if current_section == "company_overview":
            sections["company_overview"] = content
        elif current_section == "news":
            items = _extract_list_items(content)
            sections["news_summary"] = items if items else [content]
        elif current_section == "filings":
            items = _extract_list_items(content)
            sections["filings_summary"] = items if items else [content]
        elif current_section == "short":
            sections["short_interest"] = content
        elif current_section == "trader":
            sections["trader_view"] = content
        current_lines = []

    for line in lines:
        matched = False
        # Headers are typically short.
        if len(line.strip()) <= 40:
            for key, pattern in patterns.items():
                # Don't match the same section keyword if we are already in it
                if key != current_section and re.search(pattern, line, re.IGNORECASE):
                    _flush()
                    current_section = key
                    matched = True
                    break
        if not matched and current_section:
            current_lines.append(line)

    _flush()
    return sections


def _extract_list_items(text: str) -> list[str]:
    """텍스트에서 번호/불릿 리스트 항목 추출"""
    items = []
    for line in text.split("\n"):
        cleaned = re.sub(r"^[\s•\-\d.)\]]+", "", line).strip()
        if cleaned and len(cleaned) > 5:
            items.append(cleaned)
    return items[:5]  # 최대 5개
