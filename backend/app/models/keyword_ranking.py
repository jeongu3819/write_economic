from sqlalchemy import Column, Integer, String, DateTime, DECIMAL, Boolean, JSON, func
from app.database import Base


class KeywordRanking(Base):
    __tablename__ = "keyword_rankings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    week_key = Column(String(10), nullable=False)
    keyword = Column(String(200), nullable=False)
    rank_no = Column(Integer)
    final_score = Column(DECIMAL(10, 2), default=0)
    issue_score = Column(DECIMAL(10, 2), default=0)
    search_score = Column(DECIMAL(10, 2), default=0)
    competition_penalty = Column(DECIMAL(10, 2), default=0)
    search_volume = Column(Integer, default=0)
    document_count = Column(Integer, default=0)
    keyword_ratio = Column(DECIMAL(10, 4), default=0)
    related_news_count = Column(Integer, default=0)
    related_symbol_count = Column(Integer, default=0)
    summary_line = Column(String(500))
    competition_level = Column(String(10))
    recommended_channel = Column(String(20))
    is_doc_count_100k_plus = Column(Boolean, default=False)
    extra_metrics_json = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
