"""
SSE 실시간 로그 브로드캐스트 매니저
기존 server/utils/logger.js 의 Python/FastAPI 포팅
"""

import asyncio
import json
from datetime import datetime
from typing import Optional


class LogManager:
    """SSE 클라이언트에게 실시간 로그를 브로드캐스트"""

    def __init__(self):
        self._queues: list[asyncio.Queue] = []

    def add_client(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._queues.append(q)
        return q

    def remove_client(self, q: asyncio.Queue):
        if q in self._queues:
            self._queues.remove(q)

    async def broadcast(self, message: str, msg_type: str = "info"):
        prefix_map = {
            "info": "📋",
            "success": "✅",
            "error": "❌",
            "system": "⚙️",
            "warn": "⚠️",
        }
        prefix = prefix_map.get(msg_type, "📋")
        print(f"{prefix} [{msg_type.upper()}] {message}")

        data = json.dumps(
            {
                "message": message,
                "type": msg_type,
                "timestamp": datetime.now().isoformat(),
            },
            ensure_ascii=False,
        )

        dead: list[asyncio.Queue] = []
        for q in self._queues:
            try:
                q.put_nowait(f"data: {data}\n\n")
            except Exception:
                dead.append(q)
        for q in dead:
            self.remove_client(q)


# 전역 싱글톤
log_manager = LogManager()
