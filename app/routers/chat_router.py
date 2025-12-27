from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from ..deps import get_async_db, get_current_user, get_current_user_ws
from ..models import ChatRoom, ChatMessage, JobPost
from ..websocket_manager import ConnectionManager

# =========================
# REST Router
# =========================
router = APIRouter(prefix="/chat", tags=["chat"])

# =========================
# WebSocket Router
# =========================
ws_router = APIRouter(prefix="/ws", tags=["chat"])

manager = ConnectionManager()

# -------------------------------------------------
# REST: 채팅방 생성
# POST /api/chat/rooms?job_post_id=123
# -------------------------------------------------
@router.post("/rooms")
async def create_chat_room(
    job_post_id: int,
    db: AsyncSession = Depends(get_async_db),
    user=Depends(get_current_user),
):
    # 1. 공고 존재 여부 확인
    job_post = await db.get(JobPost, job_post_id)
    if not job_post:
        raise HTTPException(status_code=404, detail="Job post not found")

    # 2. 역할 분기
    if user.role == "STUDENT":
        student_id = user.id
        company_id = job_post.company_id
    elif user.role == "COMPANY":
        company_id = user.id
        student_id = None
    else:
        raise HTTPException(status_code=403, detail="Invalid user role")

    # 3. 기존 채팅방 존재 여부 확인
    stmt = select(ChatRoom).where(
        and_(
            ChatRoom.job_post_id == job_post_id,
            ChatRoom.company_id == company_id,
            ChatRoom.student_id == student_id,
        )
    )
    result = await db.execute(stmt)
    room = result.scalar_one_or_none()

    if room:
        return room

    # 4. 새 채팅방 생성
    room = ChatRoom(
        job_post_id=job_post_id,
        company_id=company_id,
        student_id=student_id,
    )
    db.add(room)
    await db.commit()
    await db.refresh(room)

    return room


# -------------------------------------------------
# REST: 내 채팅방 목록
# GET /api/chat/rooms
# -------------------------------------------------
@router.get("/rooms")
async def list_my_chat_rooms(
    db: AsyncSession = Depends(get_async_db),
    user=Depends(get_current_user),
):
    stmt = select(ChatRoom).where(
        or_(
            ChatRoom.company_id == user.id,
            ChatRoom.student_id == user.id,
        )
    )
    result = await db.execute(stmt)
    rooms = result.scalars().all()
    return rooms


# =================================================
# WebSocket: 채팅 입장
# ws://host/api/ws/chat/{chat_room_id}
# =================================================
@ws_router.websocket("/chat/{chat_room_id}")
async def chat_ws(
    websocket: WebSocket,
    chat_room_id: int,
    db: AsyncSession = Depends(get_async_db),
):
    # 1. WebSocket JWT 인증
    user = await get_current_user_ws(websocket)

    # 2. 채팅방 접근 권한 확인
    room = await db.get(ChatRoom, chat_room_id)
    if not room or user.id not in (room.company_id, room.student_id):
        await websocket.close(code=1008)
        return

    # 3. 연결 등록
    await manager.connect(chat_room_id, websocket)

    try:
        while True:
            data = await websocket.receive_json()
            content = data.get("content")

            if not content:
                continue

            # 4. 메시지 저장
            msg = ChatMessage(
                chat_room_id=chat_room_id,
                sender_id=user.id,
                content=content,
            )
            db.add(msg)
            await db.commit()
            await db.refresh(msg)

            # 5. 같은 방에 브로드캐스트
            await manager.broadcast(
                chat_room_id,
                {
                    "type": "message",
                    "id": msg.id,
                    "chat_room_id": chat_room_id,
                    "sender_id": msg.sender_id,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat(),
                },
            )

    except WebSocketDisconnect:
        manager.disconnect(chat_room_id, websocket)
