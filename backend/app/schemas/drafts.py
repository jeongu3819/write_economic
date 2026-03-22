from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DraftGenerateRequest(BaseModel):
    keyword_ranking_id: int


class BlogDraftOut(BaseModel):
    id: int
    week_key: str
    keyword_ranking_id: Optional[int] = None
    keyword: str
    title_candidates_json: Optional[list] = None
    intro_candidates_json: Optional[list] = None
    body_naver: Optional[str] = None
    body_tistory_md: Optional[str] = None
    body_tistory_html: Optional[str] = None
    summary_text: Optional[str] = None
    hashtags_json: Optional[list] = None
    caution_note: Optional[str] = None
    status: str = "draft"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
