from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.database import Base


class WeeklyRun(Base):
    __tablename__ = "weekly_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    week_key = Column(String(10), nullable=False, index=True)
    run_started_at = Column(DateTime)
    run_finished_at = Column(DateTime)
    status = Column(String(20), default="pending")
    total_source_count = Column(Integer, default=0)
    total_keyword_count = Column(Integer, default=0)
    note = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
