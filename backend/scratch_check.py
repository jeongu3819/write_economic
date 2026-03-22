import asyncio
import sys
import os

from app.services.chatgpt_browser_service import check_session

async def main():
    try:
        result = await check_session()
        print("RESULT:::", result)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
