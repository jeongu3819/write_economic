from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, func
from app.database import Base


class KeywordCandidate(Base):
    __tablename__ = "keyword_candidates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    week_key = Column(String(10), nullable=False, index=True)
    keyword = Column(String(200), nullable=False)
    origin_summary = Column(Text)
    related_news_count = Column(Integer, default=0)
    related_symbol_count = Column(Integer, default=0)
    source_item_ids_json = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())
