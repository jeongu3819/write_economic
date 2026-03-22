"""Models router — OpenAI 모델 목록 API."""
from fastapi import APIRouter
from openai import AsyncOpenAI

from app.config import OPENAI_API_KEY, OPENAI_MODEL
from app.utils.response import api_response
from app.utils.logger import get_logger

logger = get_logger("models_router")

router = APIRouter(prefix="/api", tags=["models"])

# 허용할 모델 패턴 (GPT 계열만 노출)
ALLOWED_PREFIXES = ("gpt-4", "gpt-3.5", "o1", "o3", "o4")


@router.get("/models")
async def list_models():
    """
    고정된 API 모델 목록(수집용 gpt-5.4-mini, 글작성용 gpt-5.4, 기타 gpt-4o)만 선택할 수 있도록 반환합니다.
    """
    models = [
        {"id": "gpt-5.4-mini", "owned_by": "openai"},
        {"id": "gpt-5.4", "owned_by": "openai"},
        {"id": "gpt-4o", "owned_by": "openai"},
    ]
    return api_response(data={
        "models": models,
        "default_model": OPENAI_MODEL,
    })
