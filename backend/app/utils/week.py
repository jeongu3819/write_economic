from datetime import datetime, timedelta


def get_current_week_key() -> str:
    """Return ISO week key like '2026-W12'."""
    today = datetime.now()
    iso = today.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def get_week_date_range(week_key: str) -> tuple[datetime, datetime]:
    """Return (start_of_week_monday, end_of_week_sunday) for a given week_key."""
    year, week_part = week_key.split("-W")
    year = int(year)
    week = int(week_part)
    jan4 = datetime(year, 1, 4)
    start = jan4 - timedelta(days=jan4.isoweekday() - 1) + timedelta(weeks=week - 1)
    end = start + timedelta(days=6, hours=23, minutes=59, seconds=59)
    return start, end
