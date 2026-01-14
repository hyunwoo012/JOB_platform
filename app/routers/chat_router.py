from fastapi import (  # FastAPI 컴포넌트
    APIRouter,  # 라우터
    Depends,  # 의존성
    HTTPException,  # 예외
    WebSocket,  # WebSocket
    WebSocketDisconnect,  # WS 종료 예외
)
from sqlalchemy.ext.asyncio import AsyncSession  # 비동기 세션
from sqlalchemy import select, or_  # SQLAlchemy 조회/조건

from ..deps import get_async_db, get_current_user, get_current_user_ws  # 의존성
from ..models import ChatRoom, ChatMessage  # 모델
from ..schemas import ChatRoomOut  # 스키마
from ..websocket_manager import ConnectionManager  # WS 매니저

# =========================
# REST Router
# =========================
router = APIRouter(prefix="/chat", tags=["chat"])  # /chat 라우터

# =========================
# WebSocket Router
# =========================
ws_router = APIRouter(prefix="/ws", tags=["chat"])  # /ws 라우터

manager = ConnectionManager()  # 연결 관리자

# -------------------------------------------------
# REST: 채팅방 생성 차단 (Application 기반만 허용)
# POST /api/chat/rooms
# -------------------------------------------------
@router.post("/rooms")  # 채팅방 생성 차단
async def create_chat_room_disabled():  # 핸들러
    raise HTTPException(  # 명시적 차단
        status_code=410,  # Gone
        detail="Chat rooms are created via /applications/{id}/accept only",  # 안내 메시지
    )


# -------------------------------------------------
# REST: 내 채팅방 목록
# GET /api/chat/rooms
# -------------------------------------------------
@router.get("/rooms", response_model=list[ChatRoomOut])  # 채팅방 목록
async def list_my_chat_rooms(  # 핸들러
    db: AsyncSession = Depends(get_async_db),  # DB 세션
    user=Depends(get_current_user),  # 현재 사용자
):
    stmt = select(ChatRoom).where(  # 조회 조건
        or_(  # OR 조건
            ChatRoom.company_id == user.id,  # 회사 입장
            ChatRoom.student_id == user.id,  # 학생 입장
        )
    )
    result = await db.execute(stmt)  # 조회 실행
    return result.scalars().all()  # 목록 반환


# =================================================
# WebSocket: 채팅 입장
# ws://host/api/ws/chat/{chat_room_id}?token=...
# =================================================
@ws_router.websocket("/chat/{chat_room_id}")  # WS 라우트
async def chat_ws(  # WS 핸들러
    websocket: WebSocket,  # 소켓
    chat_room_id: int,  # 채팅방 ID
    db: AsyncSession = Depends(get_async_db),  # DB 세션
):
    await websocket.accept()  # 연결 수락

    user = await get_current_user_ws(websocket)  # WS 사용자 인증

    room = await db.get(ChatRoom, chat_room_id)  # 채팅방 조회
    if not room or user.id not in (room.company_id, room.student_id):  # 접근 권한 확인
        await websocket.close(code=1008)  # 정책 위반 종료
        return  # 종료

    await manager.connect(chat_room_id, websocket)  # 연결 등록

    try:
        while True:  # 메시지 루프
            data = await websocket.receive_json()  # JSON 수신
            content = data.get("content")  # 메시지 내용

            if not content:  # 내용 없으면
                continue  # 무시

            msg = ChatMessage(  # 메시지 생성
                chat_room_id=chat_room_id,  # 방 ID
                sender_id=user.id,  # 발신자
                content=content,  # 내용
            )
            db.add(msg)  # 세션 추가
            await db.commit()  # 커밋
            await db.refresh(msg)  # DB 반영

            await manager.broadcast(  # 브로드캐스트
                chat_room_id,  # 방 ID
                {
                    "type": "message",  # 메시지 타입
                    "id": msg.id,  # 메시지 ID
                    "chat_room_id": chat_room_id,  # 방 ID
                    "sender_id": msg.sender_id,  # 발신자 ID
                    "content": msg.content,  # 내용
                    "created_at": msg.created_at.isoformat(),  # 시각
                },
            )

    except WebSocketDisconnect:
        manager.disconnect(chat_room_id, websocket)  # 연결 해제
