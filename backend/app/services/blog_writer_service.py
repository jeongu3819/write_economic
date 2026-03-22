"""
블로그 글 생성 서비스
ChatGPT/newstock 원문 응답을 블로그 형태로 재구성
"""

from datetime import datetime
from app.utils.parser import extract_plain_text, parse_sections


def generate_blog(ticker: str, raw_response: str) -> dict:
    """
    ChatGPT 원문 응답을 블로그 형태로 재구성.

    Returns:
        {
            "blog_title": str,
            "blog_content": str (HTML),
            "sections": dict,
        }
    """
    plain_text = extract_plain_text(raw_response)
    sections = parse_sections(plain_text)

    today = datetime.now().strftime("%Y년 %m월 %d일")
    blog_title = f"{ticker} 분석: 최근 뉴스와 공시를 통해 본 핵심 포인트"

    # ── HTML 블로그 본문 생성 ──
    html_parts = []

    # 제목
    html_parts.append(f'<h1 class="blog-title">📊 {blog_title}</h1>')
    html_parts.append(f'<p class="blog-date">분석 날짜: {today}</p>')

    # 서론
    html_parts.append('<div class="blog-section blog-intro">')
    html_parts.append(f"<h2>🔍 오늘의 {ticker} 핵심 포인트</h2>")
    if sections["company_overview"]:
        intro_text = sections["company_overview"][:200]
        if len(sections["company_overview"]) > 200:
            intro_text += "..."
        html_parts.append(f"<p>{_escape_html(intro_text)}</p>")
    else:
        html_parts.append(
            f"<p>오늘 {ticker} 종목에 대한 주요 분석 내용을 정리했습니다. "
            "기업 개요부터 최신 뉴스, 공시, 공매도 비율, "
            "그리고 트레이더 관점까지 살펴보겠습니다.</p>"
        )
    html_parts.append("</div>")

    # 기업 개요
    html_parts.append('<div class="blog-section">')
    html_parts.append("<h2>🏢 기업 개요</h2>")
    if sections["company_overview"]:
        html_parts.append(f"<p>{_escape_html(sections['company_overview'])}</p>")
    else:
        html_parts.append(f"<p>{ticker}에 대한 기업 개요 정보입니다.</p>")
    html_parts.append("</div>")

    # 최신 뉴스
    html_parts.append('<div class="blog-section">')
    html_parts.append("<h2>📰 최신 뉴스 요약</h2>")
    if sections["news_summary"]:
        html_parts.append("<ul>")
        for news in sections["news_summary"][:3]:
            html_parts.append(f"<li>{_escape_html(news)}</li>")
        html_parts.append("</ul>")
    else:
        html_parts.append("<p>분석 시점에 수집된 최신 뉴스입니다.</p>")
    html_parts.append("</div>")

    # 최신 공시
    html_parts.append('<div class="blog-section">')
    html_parts.append("<h2>📋 최신 공시 요약</h2>")
    if sections["filings_summary"]:
        html_parts.append("<ul>")
        for filing in sections["filings_summary"][:3]:
            html_parts.append(f"<li>{_escape_html(filing)}</li>")
        html_parts.append("</ul>")
    else:
        html_parts.append("<p>분석 시점에 수집된 최신 공시입니다.</p>")
    html_parts.append("</div>")

    # 공매도 비율
    html_parts.append('<div class="blog-section">')
    html_parts.append("<h2>📉 공매도 비율 해석</h2>")
    if sections["short_interest"]:
        html_parts.append(f"<p>{_escape_html(sections['short_interest'])}</p>")
    else:
        html_parts.append("<p>공매도 관련 데이터를 확인해주세요.</p>")
    html_parts.append("</div>")

    # 트레이더 관점
    html_parts.append('<div class="blog-section">')
    html_parts.append("<h2>💡 트레이더 관점 해석</h2>")
    if sections["trader_view"]:
        html_parts.append(f"<p>{_escape_html(sections['trader_view'])}</p>")
    else:
        html_parts.append("<p>단기 트레이딩 관점의 분석입니다.</p>")
    html_parts.append("</div>")

    # 결론
    html_parts.append('<div class="blog-section blog-conclusion">')
    html_parts.append("<h2>📌 종합 정리</h2>")
    html_parts.append(
        f"<p>{ticker}에 대한 오늘의 분석을 종합하면, "
        "최신 뉴스와 공시, 공매도 데이터, 그리고 시장 심리를 고려하여 "
        "투자 판단에 참고해야 할 포인트들을 정리했습니다. "
        "위 내용은 참고용으로만 활용하시기 바랍니다.</p>"
    )
    html_parts.append("</div>")

    # 면책 조항
    html_parts.append('<div class="blog-disclaimer">')
    html_parts.append(
        "<p>⚠️ <strong>면책 조항</strong>: 본 분석은 정보 제공 목적으로만 "
        "작성되었으며, 투자 권유가 아닙니다. "
        "투자에 따른 모든 책임은 투자자 본인에게 있습니다.</p>"
    )
    html_parts.append("</div>")

    blog_content = "\n".join(html_parts)

    return {
        "blog_title": blog_title,
        "blog_content": blog_content,
        "sections": sections,
    }


def _escape_html(text: str) -> str:
    """기본 HTML 이스케이프 (이미 textContent에서 추출된 텍스트 대상)"""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br>")
    )
