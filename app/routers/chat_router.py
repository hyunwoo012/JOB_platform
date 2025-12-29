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
from ..schemas import ChatRoomCreate, ChatRoomOut
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
# REST: 채팅방 생성 (JSON body)
# POST /api/chat/rooms
# -------------------------------------------------
@router.post("/rooms", response_model=ChatRoomOut)
async def create_chat_room(
    payload: ChatRoomCreate,
    db: AsyncSession = Depends(get_async_db),
    user=Depends(get_current_user),
):
    job_post_id = payload.job_post_id
    student_id = payload.student_id

    # 1. 공고 존재 여부
    job_post = await db.get(JobPost, job_post_id)
    if not job_post:
        raise HTTPException(status_code=404, detail="Job post not found")

    # 2. 역할 분기
    if user.role == "STUDENT":
        if user.id != student_id:
            raise HTTPException(status_code=403, detail="Invalid student_id")
        company_id = job_post.company_id

    elif user.role == "COMPANY":
        company_id = user.id

    else:
        raise HTTPException(status_code=403, detail="Invalid user role")

    # 3. 기존 채팅방 확인
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

    # 4. 채팅방 생성
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
@router.get("/rooms", response_model=list[ChatRoomOut])
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
    return result.scalars().all()


# =================================================
# WebSocket: 채팅 입장
# ws://host/api/ws/chat/{chat_room_id}?token=...
# =================================================
@ws_router.websocket("/chat/{chat_room_id}")
async def chat_ws(
    websocket: WebSocket,
    chat_room_id: int,
    db: AsyncSession = Depends(get_async_db),
):
    # ✅ 1. 반드시 먼저 accept
    await websocket.accept()

    # ✅ 2. WebSocket JWT 인증
    user = await get_current_user_ws(websocket)

    # 3. 채팅방 접근 권한 확인
    room = await db.get(ChatRoom, chat_room_id)
    if not room or user.id not in (room.company_id, room.student_id):
        await websocket.close(code=1008)
        return

    # 4. 연결 등록
    await manager.connect(chat_room_id, websocket)

    try:
        while True:
            data = await websocket.receive_json()
            content = data.get("content")

            if not content:
                continue

            # 5. 메시지 저장
            msg = ChatMessage(
                chat_room_id=chat_room_id,
                sender_id=user.id,
                content=content,
            )
            db.add(msg)
            await db.commit()
            await db.refresh(msg)

            # 6. 같은 방 전체 브로드캐스트
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
