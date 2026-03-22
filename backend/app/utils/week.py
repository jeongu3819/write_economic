"""
주간 범위 계산 유틸리티
- Asia/Seoul 타임존 기준
- 월요일 00:00:00 ~ 일요일 23:59:59
"""
from datetime import datetime, timedelta, timezone

# Asia/Seoul = UTC+9 (DST 없음)
KST = timezone(timedelta(hours=9))


def now_kst() -> datetime:
    """현재 KST 시각."""
    return datetime.now(KST)


def get_current_week_key() -> str:
    """Return today's date as key for rolling 7-day window."""
    today = now_kst()
    return today.strftime("%Y-%m-%d")


def get_week_date_range(week_key: str) -> tuple[datetime, datetime]:
    """
    Return (start, end) for a given week_key.
    
    If week_key is ISO week like '2026-W12', use Monday-Sunday.
    If week_key is '2026-03-23', use rolling 7-day window ending on that date.
    """
    if "-W" in week_key:
        year, week_part = week_key.split("-W")
        year = int(year)
        week = int(week_part)
        jan4 = datetime(year, 1, 4, tzinfo=KST)
        start_of_w1 = jan4 - timedelta(days=jan4.isoweekday() - 1)
        start = start_of_w1 + timedelta(weeks=week - 1)
        end = start + timedelta(days=6, hours=23, minutes=59, seconds=59)
        return start, end
    else:
        # Rolling 7-day window
        end_date = datetime.strptime(week_key, "%Y-%m-%d").replace(tzinfo=KST)
        end = end_date.replace(hour=23, minute=59, second=59)
        start = (end - timedelta(days=6)).replace(hour=0, minute=0, second=0)
        return start, end


def get_week_display(week_key: str) -> str:
    """
    주차의 날짜 범위를 표시 문자열로 반환.
    예: '2026-W12' → '2026-03-16 ~ 2026-03-22'
    """
    start, end = get_week_date_range(week_key)
    return f"{start.strftime('%Y-%m-%d')} ~ {end.strftime('%Y-%m-%d')}"


def get_week_info() -> dict:
    """현재 주차 정보를 딕셔너리로 반환."""
    week_key = get_current_week_key()
    start, end = get_week_date_range(week_key)
    return {
        "week_key": week_key,
        "start_date": start.strftime("%Y-%m-%d"),
        "end_date": end.strftime("%Y-%m-%d"),
        "display": get_week_display(week_key),
    }
