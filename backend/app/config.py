import os
from dotenv import load_dotenv

load_dotenv()

# --- Database ---
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "economy_blog")

DATABASE_URL = (
    f"mysql+aiomysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    "?charset=utf8mb4"
)

# --- OpenAI ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4-mini")  # 키워드 수집/분류용
OPENAI_DRAFT_MODEL = os.getenv("OPENAI_DRAFT_MODEL", "gpt-5.4")  # 글쓰기 작성용

# --- Server ---
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))

# --- Scoring Weights ---
SCORING_WEIGHTS = {
    "issue": float(os.getenv("SCORE_WEIGHT_ISSUE", "1.0")),
    "search": float(os.getenv("SCORE_WEIGHT_SEARCH", "1.5")),
    "competition": float(os.getenv("SCORE_WEIGHT_COMPETITION", "0.8")),
    "news_factor": 3,
    "symbol_factor": 5,
    "filing_factor": 2,
}
