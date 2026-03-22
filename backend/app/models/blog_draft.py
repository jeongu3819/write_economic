from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, func
from app.database import Base


class BlogDraft(Base):
    __tablename__ = "blog_drafts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    week_key = Column(String(10), nullable=False, index=True)
    keyword_ranking_id = Column(Integer, ForeignKey("keyword_rankings.id", ondelete="SET NULL"))
    keyword = Column(String(200), nullable=False)
    title_candidates_json = Column(JSON)
    intro_candidates_json = Column(JSON)
    body_naver = Column(Text)
    body_tistory_md = Column(Text)
    body_tistory_html = Column(Text)
    summary_text = Column(Text)
    hashtags_json = Column(JSON)
    caution_note = Column(Text)
    status = Column(String(20), default="draft")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
