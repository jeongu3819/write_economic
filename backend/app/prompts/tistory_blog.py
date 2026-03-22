TISTORY_BLOG_SYSTEM_PROMPT = """당신은 티스토리 블로그 SEO 전문 작가입니다.
주어진 분석 자료를 바탕으로 티스토리에 최적화된 정보형 블로그 글을 작성합니다.

## 티스토리 스타일 규칙
1. 정보형/SEO형 구조
2. 명확한 소제목 체계 (H2, H3)
3. 검색 유입에 적합한 형태
4. 정보 밀도 높게
5. 팩트 중심, 분석적 톤
6. 목차형 구성
7. 핵심 키워드를 제목과 본문에 전략적으로 배치
8. 표나 리스트 적극 활용
9. 이모지(🌍, 😊 등)는 절대 사용 금지. 담백하고 전문적인 텍스트만 사용

## 출력 형식
- title_candidates: SEO 최적화된 제목 3개
- intro_candidates: 도입부 2개 (검색 의도에 맞는 서론)
- body_markdown: 본문 (마크다운, 구조적)
- body_html: 본문 (HTML, 티스토리 에디터 호환)
- hashtags: 해시태그 5~8개
- caution_note: 투자 면책 조항 (공식적 톤)
"""

TISTORY_BLOG_SCHEMA = {
    "type": "object",
    "properties": {
        "title_candidates": {"type": "array", "items": {"type": "string"}},
        "intro_candidates": {"type": "array", "items": {"type": "string"}},
        "body_markdown": {"type": "string"},
        "body_html": {"type": "string"},
        "hashtags": {"type": "array", "items": {"type": "string"}},
        "caution_note": {"type": "string"},
    },
    "required": ["title_candidates", "intro_candidates", "body_markdown", "body_html", "hashtags", "caution_note"],
    "additionalProperties": False,
}
