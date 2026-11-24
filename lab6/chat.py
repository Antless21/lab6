"""Общий чат одного процесса FastAPI; сообщения не сохраняются в БД."""

import asyncio
from datetime import datetime, timezone

from fastapi import WebSocket, WebSocketDisconnect


class ConnectionManager:
    def __init__(self):
        self.connections: set[WebSocket] = set()
        # Сериализация отправки, в том числе при одновременных сообщениях.
        self.lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self.lock:
            self.connections.add(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self.lock:
            self.connections.discard(websocket)

    async def send(self, websocket: WebSocket, payload: dict) -> None:
        async with self.lock:
            await websocket.send_json(payload)

    async def broadcast(self, payload: dict) -> None:
        async with self.lock:
            for websocket in tuple(self.connections):
                try:
                    await websocket.send_json(payload)
                except (WebSocketDisconnect, OSError, RuntimeError):
                    self.connections.discard(websocket)


async def run_chat(websocket: WebSocket, manager: ConnectionManager) -> None:
    name = websocket.query_params.get("name", "").strip()
    if not 1 <= len(name) <= 50:
        await websocket.close(code=1008, reason="Имя: от 1 до 50 символов")
        return

    await manager.connect(websocket)
    try:
        await manager.send(
            websocket, {"type": "system", "text": f"Вы вошли как {name}."}
        )
        while True:
            frame = await websocket.receive()
            if frame["type"] == "websocket.disconnect":
                break
            text = frame.get("text")
            if text is None:
                await manager.send(
                    websocket,
                    {"type": "error", "text": "Отправьте текстовое сообщение."},
                )
                continue
            text = text.strip()
            if not 1 <= len(text) <= 1000:
                await manager.send(
                    websocket,
                    {"type": "error", "text": "Сообщение: от 1 до 1000 символов."},
                )
                continue
            await manager.broadcast(
                {
                    "type": "message",
                    "name": name,
                    "text": text,
                    "time": datetime.now(timezone.utc).isoformat(),
                }
            )
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(websocket)
