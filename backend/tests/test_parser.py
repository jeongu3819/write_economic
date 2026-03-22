"""
파서 유틸리티 단위 테스트
"""

import pytest
from app.utils.parser import clean_response_text, extract_plain_text, parse_sections


class TestCleanResponseText:
    def test_removes_copy_code(self):
        text = "some code Copy code more text"
        result = clean_response_text(text)
        assert "Copy code" not in result

    def test_removes_button_tags(self):
        text = "before <button>Click</button> after"
        result = clean_response_text(text)
        assert "<button" not in result
        assert "before" in result
        assert "after" in result

    def test_empty_input(self):
        assert clean_response_text("") == ""
        assert clean_response_text(None) == ""


class TestExtractPlainText:
    def test_removes_html_tags(self):
        html = "<p>Hello <b>world</b></p>"
        result = extract_plain_text(html)
        assert "Hello" in result
        assert "world" in result
        assert "<" not in result

    def test_preserves_line_breaks(self):
        html = "<p>Line 1</p><p>Line 2</p>"
        result = extract_plain_text(html)
        assert "Line 1" in result
        assert "Line 2" in result

    def test_handles_entities(self):
        html = "&amp; &lt; &gt; &nbsp; &#39; &quot;"
        result = extract_plain_text(html)
        assert "&" in result
        assert "<" in result
        assert ">" in result


class TestParseSections:
    def test_parses_all_sections(self):
        text = """
        기업 개요
        AMD는 반도체 기업입니다.

        최신 뉴스
        1. 뉴스 항목 1번 내용입니다
        2. 뉴스 항목 2번 내용입니다
        3. 뉴스 항목 3번 내용입니다

        최신 공시
        1. 공시 항목 1번 내용입니다
        2. 공시 항목 2번 내용입니다

        공매도 비율
        현재 공매도 비율은 3.5%입니다.

        트레이더 해석
        단기적으로 매수 추천입니다.
        """
        result = parse_sections(text)
        assert result["company_overview"]
        assert len(result["news_summary"]) >= 2
        assert len(result["filings_summary"]) >= 1
        assert result["short_interest"]
        assert result["trader_view"]

    def test_empty_text(self):
        result = parse_sections("")
        assert result["company_overview"] == ""
        assert result["news_summary"] == []
        assert result["filings_summary"] == []

    def test_partial_sections(self):
        text = """
        기업 개요
        간단한 기업 소개글입니다.

        공매도 비율
        공매도가 높습니다.
        """
        result = parse_sections(text)
        assert result["company_overview"]
        assert result["short_interest"]
        assert result["news_summary"] == []
