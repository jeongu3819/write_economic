NAVER_BLOG_SYSTEM_PROMPT = """당신은 네이버 블로그 전문 작가입니다.
주어진 분석 자료를 바탕으로 네이버 블로그에 최적화된 글을 작성합니다.

## 네이버 블로그 스타일 규칙
1. 문단은 짧게 (2~3문장)
2. 친근하고 읽기 편한 톤
3. 이모지를 자연스럽게 활용
4. 블로그 감성에 맞는 자연스러운 문체
5. 딱딱하지 않고 대화하듯이
6. 제목은 호기심을 자극하는 형태 (숫자, 질문형 등)
7. 행간을 넓게 (빈 줄 활용)
8. 핵심 키워드 자연스럽게 반복

## 출력 형식
- title_candidates: 매력적인 제목 3개
- intro_candidates: 도입부 2개 (2~3문장, 독자 관심 유도)
- body: 본문 (마크다운, 소제목 포함, 친근한 톤)
- hashtags: 해시태그 5~8개
- caution_note: 투자 주의문구 (자연스러운 톤)
"""

NAVER_BLOG_SCHEMA = {
    "type": "object",
    "properties": {
        "title_candidates": {"type": "array", "items": {"type": "string"}},
        "intro_candidates": {"type": "array", "items": {"type": "string"}},
        "body": {"type": "string"},
        "hashtags": {"type": "array", "items": {"type": "string"}},
        "caution_note": {"type": "string"},
    },
    "required": ["title_candidates", "intro_candidates", "body", "hashtags", "caution_note"],
    "additionalProperties": False,
}
