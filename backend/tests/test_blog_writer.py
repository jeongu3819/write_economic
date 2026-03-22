"""
블로그 생성 서비스 단위 테스트
"""

import pytest
from app.services.blog_writer_service import generate_blog


class TestGenerateBlog:
    def test_basic_generation(self):
        raw = """
        기업 개요
        AMD는 미국 반도체 회사입니다. CPU 및 GPU를 설계합니다.

        최신 뉴스
        1. AMD가 새로운 AI 칩을 발표했습니다.
        2. AMD 주가가 5% 상승했습니다.
        3. AMD와 Microsoft의 파트너십 확대 소식.

        최신 공시
        1. 분기별 실적 보고서 발표
        2. 자사주 매입 프로그램 발표
        3. SEC 정기 공시 제출

        공매도 비율
        현재 공매도 비율은 3.5%로 비교적 낮은 수준입니다.

        트레이더 해석
        단기적으로 상승 모멘텀이 있으며, AI 테마 수혜주로 관심이 필요합니다.
        """
        result = generate_blog("AMD", raw)

        assert result["blog_title"]
        assert "AMD" in result["blog_title"]
        assert result["blog_content"]
        assert "<h1" in result["blog_content"]
        assert "<h2" in result["blog_content"]
        assert result["sections"]

    def test_empty_response(self):
        result = generate_blog("AAPL", "")
        assert result["blog_title"]
        assert "AAPL" in result["blog_title"]
        assert result["blog_content"]

    def test_sections_parsing(self):
        raw = """
        기업 개요
        테슬라는 전기차 제조업체입니다.

        최신 뉴스
        - 테슬라 Model Y 판매 증가
        - 자율주행 소프트웨어 업데이트
        - 중국 시장 확대

        공매도 비율
        공매도 비율 2.1%

        트레이더 해석
        강한 매수 시그널이 보입니다.
        """
        result = generate_blog("TSLA", raw)
        sections = result["sections"]

        assert sections.get("company_overview")
        assert "테슬라" in sections["company_overview"]
        assert len(sections.get("news_summary", [])) > 0
        assert sections.get("short_interest")
        assert sections.get("trader_view")

    def test_html_stripping_and_escaping(self):
        raw = """
        기업 개요
        <script>alert('xss')</script> 테스트 기업입니다. A & B < C.
        """
        result = generate_blog("TEST", raw)
        # The parser strips <script> entirely
        assert "<script>" not in result["blog_content"]
        assert "alert('xss')" in result["blog_content"]
        # & should be escaped to &amp; and < C to &lt; C
        assert "A &amp; B" in result["blog_content"]
