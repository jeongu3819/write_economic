from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean, func
from app.database import Base


class PromptTemplate(Base):
    __tablename__ = "prompt_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    template_name = Column(String(100), nullable=False)
    template_type = Column(String(30), nullable=False)
    version = Column(Integer, default=1)
    system_prompt = Column(Text, nullable=False)
    schema_json = Column(JSON)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
