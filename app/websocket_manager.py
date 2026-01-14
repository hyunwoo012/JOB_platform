from typing import Dict, List  # 타입 힌트
from fastapi import WebSocket  # WebSocket 타입


class ConnectionManager:  # WS 연결 관리 클래스
    def __init__(self):  # 생성자
        self.active_connections: Dict[int, List[WebSocket]] = {}  # room_id -> 소켓 목록

    async def connect(self, room_id: int, websocket: WebSocket):  # 연결 추가
        """
        채팅방에 WebSocket 연결 추가
        """  # 함수 설명

        if room_id not in self.active_connections:  # 방이 없으면
            self.active_connections[room_id] = []  # 목록 생성

        self.active_connections[room_id].append(websocket)  # 소켓 추가

    def disconnect(self, room_id: int, websocket: WebSocket):  # 연결 제거
        """
        채팅방에서 WebSocket 연결 제거
        """  # 함수 설명
        if room_id not in self.active_connections:  # 방이 없으면
            return  # 종료

        connections = self.active_connections[room_id]  # 현재 방의 소켓들

        if websocket in connections:  # 소켓이 존재하면
            connections.remove(websocket)  # 목록에서 제거

        if not connections:  # 방이 비었으면
            del self.active_connections[room_id]  # 방 자체 제거

    async def broadcast(self, room_id: int, message: dict):  # 브로드캐스트
        """
        채팅방에 연결된 모든 클라이언트에게 메시지 전송
        """  # 함수 설명
        if room_id not in self.active_connections:  # 방이 없으면
            return  # 종료

        for ws in list(self.active_connections[room_id]):  # 복사본으로 순회
            try:
                await ws.send_json(message)  # JSON 전송
            except Exception:
                self.disconnect(room_id, ws)  # 실패 소켓 정리
