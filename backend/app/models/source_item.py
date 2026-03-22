from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, func
from app.database import Base


class SourceItem(Base):
    __tablename__ = "source_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    week_key = Column(String(10), nullable=False, index=True)
    source_type = Column(String(20), nullable=False)
    source_site = Column(String(30), nullable=False)
    title = Column(String(500), nullable=False)
    summary = Column(Text)
    url = Column(String(2000))
    published_at = Column(DateTime)
    raw_text = Column(Text)
    normalized_topic = Column(String(200))
    related_symbols_json = Column(JSON)
    related_industries_json = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())
