from typing import Dict, Set
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # room_id -> set of WebSocket
        self.active_connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, room_id: int, websocket: WebSocket):
        """
        채팅방에 WebSocket 연결 추가
        """
        await websocket.accept()

        if room_id not in self.active_connections:
            self.active_connections[room_id] = set()

        self.active_connections[room_id].add(websocket)

    def disconnect(self, room_id: int, websocket: WebSocket):
        """
        채팅방에서 WebSocket 연결 제거
        """
        if room_id in self.active_connections:
            self.active_connections[room_id].discard(websocket)

            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    async def broadcast(self, room_id: int, message: dict):
        """
        채팅방에 연결된 모든 클라이언트에게 메시지 전송
        """
        if room_id not in self.active_connections:
            return

        for ws in self.active_connections[room_id]:
            await ws.send_json(message)
