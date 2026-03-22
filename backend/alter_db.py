import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "root")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "economy_blog")

DATABASE_URL = f"mysql+aiomysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_async_engine(DATABASE_URL, echo=True)

async def alter_tables():
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE keyword_candidates ADD COLUMN keyword_type VARCHAR(50);"))
            await conn.execute(text("ALTER TABLE keyword_candidates ADD COLUMN recommendation_reasons_json JSON;"))
            print("Successfully added columns to keyword_candidates")
        except Exception as e:
            print(f"Skipped keyword_candidates alter: {e}")
            
        try:
            await conn.execute(text("ALTER TABLE keyword_rankings ADD COLUMN keyword_type VARCHAR(50);"))
            await conn.execute(text("ALTER TABLE keyword_rankings ADD COLUMN recommendation_reasons_json JSON;"))
            print("Successfully added columns to keyword_rankings")
        except Exception as e:
            print(f"Skipped keyword_rankings alter: {e}")

asyncio.run(alter_tables())
