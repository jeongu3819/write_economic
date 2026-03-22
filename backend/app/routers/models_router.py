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
    OpenAI API에서 사용 가능한 모델 목록을 가져옵니다.
    실패 시 기본 모델만 반환합니다.
    """
    try:
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        response = await client.models.list()

        models = []
        for m in response.data:
            if any(m.id.startswith(prefix) for prefix in ALLOWED_PREFIXES):
                models.append({
                    "id": m.id,
                    "owned_by": m.owned_by,
                })

        # 정렬: gpt-4o를 앞에
        models.sort(key=lambda x: (
            0 if x["id"] == OPENAI_MODEL else
            1 if "gpt-4o" in x["id"] else
            2 if "gpt-4" in x["id"] else
            3
        ))

        return api_response(data={
            "models": models,
            "default_model": OPENAI_MODEL,
        })

    except Exception as e:
        logger.warning(f"Failed to fetch models: {e}")
        # Fallback: 기본 모델만 반환
        return api_response(data={
            "models": [
                {"id": OPENAI_MODEL, "owned_by": "openai"},
                {"id": "gpt-4o-mini", "owned_by": "openai"},
            ],
            "default_model": OPENAI_MODEL,
        })
