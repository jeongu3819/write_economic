from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PromptCreateRequest(BaseModel):
    template_name: str
    template_type: str
    system_prompt: str
    template_schema_json: Optional[dict] = None


class PromptUpdateRequest(BaseModel):
    template_name: Optional[str] = None
    system_prompt: Optional[str] = None
    template_schema_json: Optional[dict] = None
    is_active: Optional[bool] = None


class PromptTemplateOut(BaseModel):
    id: int
    template_name: str
    template_type: str
    version: int
    system_prompt: str
    template_schema_json: Optional[dict] = None
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
