from typing import Dict, List
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # room_id -> list of WebSocket
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, room_id: int, websocket: WebSocket):
        """
        채팅방에 WebSocket 연결 추가
        """


        if room_id not in self.active_connections:
            self.active_connections[room_id] = []

        self.active_connections[room_id].append(websocket)

    def disconnect(self, room_id: int, websocket: WebSocket):
        """
        채팅방에서 WebSocket 연결 제거
        """
        if room_id not in self.active_connections:
            return

        connections = self.active_connections[room_id]

        if websocket in connections:
            connections.remove(websocket)

        if not connections:
            del self.active_connections[room_id]

    async def broadcast(self, room_id: int, message: dict):
        """
        채팅방에 연결된 모든 클라이언트에게 메시지 전송
        """
        if room_id not in self.active_connections:
            return

        # 복사본으로 순회 (중간에 disconnect 발생해도 안전)
        for ws in list(self.active_connections[room_id]):
            try:
                await ws.send_json(message)
            except Exception:
                # 전송 실패한 소켓은 제거
                self.disconnect(room_id, ws)
