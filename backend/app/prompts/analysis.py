ANALYSIS_SYSTEM_PROMPT = """당신은 주식/경제 뉴스 분석 전문가입니다.
주어진 키워드와 관련 뉴스/이슈 데이터를 분석하여, 블로그 글 작성을 위한 구조화된 분석 자료를 생성해주세요.

## 규칙
1. 핵심 관점(core_angle)은 독자의 관심을 끌 수 있는 흥미로운 시각이어야 합니다.
2. 근거 포인트(supporting_points)는 3~5개, 구체적 수치나 팩트 기반이어야 합니다.
3. 출처 요약(source_summary)은 분석에 사용된 뉴스/데이터의 핵심을 2~3줄로 정리합니다.
4. 투자자 주의사항(investor_caution)은 리스크 요인을 반드시 포함합니다.
5. 태그(tags)는 블로그 해시태그용으로 5~8개를 생성합니다.
6. 반드시 한국어로 작성합니다.
"""

ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "keyword": {"type": "string"},
        "core_angle": {"type": "string"},
        "supporting_points": {"type": "array", "items": {"type": "string"}},
        "source_summary": {"type": "string"},
        "investor_caution": {"type": "string"},
        "tags": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["keyword", "core_angle", "supporting_points", "source_summary", "investor_caution", "tags"],
    "additionalProperties": False,
}
