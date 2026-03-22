from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal


class KeywordGenerateRequest(BaseModel):
    week_key: str


class RerankRequest(BaseModel):
    weight_issue: float = 1.0
    weight_search: float = 1.5
    weight_competition: float = 0.8


class KeywordRankingOut(BaseModel):
    id: int
    week_key: str
    keyword: str
    rank_no: Optional[int] = None
    final_score: Optional[float] = None
    issue_score: Optional[float] = None
    search_score: Optional[float] = None
    competition_penalty: Optional[float] = None
    search_volume: int = 0
    document_count: int = 0
    keyword_ratio: Optional[float] = None
    related_news_count: int = 0
    related_symbol_count: int = 0
    summary_line: Optional[str] = None
    competition_level: Optional[str] = None
    recommended_channel: Optional[str] = None
    is_doc_count_100k_plus: bool = False
    extra_metrics_json: Optional[dict] = None

    class Config:
        from_attributes = True
