from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class CollectRequest(BaseModel):
    week_key: Optional[str] = None


class WeeklyRunOut(BaseModel):
    id: int
    week_key: str
    status: str
    total_source_count: int
    total_keyword_count: int
    run_started_at: Optional[datetime] = None
    run_finished_at: Optional[datetime] = None
    note: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SourceItemOut(BaseModel):
    id: int
    week_key: str
    source_type: str
    source_site: str
    title: str
    summary: Optional[str] = None
    url: Optional[str] = None
    published_at: Optional[datetime] = None
    normalized_topic: Optional[str] = None
    related_symbols_json: Optional[list] = None
    related_industries_json: Optional[list] = None

    class Config:
        from_attributes = True
