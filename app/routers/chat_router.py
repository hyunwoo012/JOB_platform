from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..deps import get_async_db, get_current_user_ws
from ..models import ChatRoom, ChatMessage, ChatReadStatus
from ..websocket_manager import ConnectionManager

router = APIRouter(prefix="/ws", tags=["chat"])

manager = ConnectionManager()


@router.websocket("/chat/{chat_room_id}")
async def chat_ws(
    websocket: WebSocket,
    chat_room_id: int,
    db: AsyncSession = Depends(get_async_db),
):
    # 1. WebSocket JWT 인증
    user = await get_current_user_ws(websocket)

    # 2. 채팅방 확인
    room = await db.get(ChatRoom, chat_room_id)
    if not room or user.id not in (room.company_id, room.student_id):
        await websocket.close(code=1008)
        return

    # 3. ConnectionManager에 등록
    await manager.connect(chat_room_id, websocket)

    try:
        while True:
            # 4. 메시지 수신
            data = await websocket.receive_json()
            content = data["content"]

            # 5. DB 저장
            msg = ChatMessage(
                chat_room_id=chat_room_id,
                sender_id=user.id,
                content=content,
            )
            db.add(msg)
            await db.commit()
            await db.refresh(msg)

            # 6. 읽음 처리 (간단 버전)
            await db.execute(
                select(ChatReadStatus).where(
                    ChatReadStatus.user_id == user.id,
                    ChatReadStatus.chat_room_id == chat_room_id,
                )
            )

            # 7. 같은 방 전체에게 push
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
        print(f"user {user.id} disconnected from room {chat_room_id}")
