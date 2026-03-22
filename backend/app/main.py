from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import issues, keywords, drafts, prompts
from app.utils.response import api_response

app = FastAPI(
    title="Economy Blog Platform",
    description="주간 이슈 수집 → 키워드 랭킹 → 블로그 초안 생성 플랫폼",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(issues.router)
app.include_router(keywords.router)
app.include_router(drafts.router)
app.include_router(prompts.router)


@app.get("/api/health")
async def health():
    return api_response(data={"status": "ok", "service": "Economy Blog Platform"})
