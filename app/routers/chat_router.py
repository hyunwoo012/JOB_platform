from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..deps import get_db, get_current_user, require_role
from ..models import User, UserRole, ChatRoom, ChatMessage, ChatReadStatus, JobPost
from ..schemas import ChatRoomCreate, ChatRoomOut, ChatMessageCreate, ChatMessageOut

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/rooms", response_model=ChatRoomOut)
def create_chat_room(
    payload: ChatRoomCreate,
    user: User = Depends(require_role(UserRole.COMPANY)),
    db: Session = Depends(get_db),
):
    job = db.get(JobPost, payload.job_post_id)
    if not job or job.is_deleted:
        raise HTTPException(status_code=404, detail="Job post not found")
    if job.company_id != user.id:
        raise HTTPException(status_code=403, detail="Not your job post")

    # 이미 있으면 반환
    room = (
        db.query(ChatRoom)
        .filter(
            ChatRoom.job_post_id == payload.job_post_id,
            ChatRoom.company_id == user.id,
            ChatRoom.student_id == payload.student_id,
        )
        .first()
    )
    if room:
        return room

    room = ChatRoom(
        job_post_id=payload.job_post_id,
        company_id=user.id,
        student_id=payload.student_id,
    )
    db.add(room)

    # 읽음 상태 기본값 생성 (선택)
    db.add(ChatReadStatus(user_id=user.id, chat_room=room))
    db.add(ChatReadStatus(user_id=payload.student_id, chat_room=room))

    db.commit()
    db.refresh(room)
    return room


@router.get("/rooms", response_model=list[ChatRoomOut])
def list_my_chat_rooms(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(ChatRoom)
    if user.role == UserRole.COMPANY:
        q = q.filter(ChatRoom.company_id == user.id)
    else:
        q = q.filter(ChatRoom.student_id == user.id)
    return q.order_by(ChatRoom.created_at.desc()).all()


@router.post("/rooms/{chat_room_id}/messages", response_model=ChatMessageOut)
def send_message(
    chat_room_id: int,
    payload: ChatMessageCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    room = db.get(ChatRoom, chat_room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Chat room not found")

    # 방 참여자만 메시지 가능
    if user.id not in (room.company_id, room.student_id):
        raise HTTPException(status_code=403, detail="Not a participant")

    msg = ChatMessage(chat_room_id=chat_room_id, sender_id=user.id, content=payload.content)
    db.add(msg)

    room.last_message_at = msg.created_at  # DB default가 있으니 commit 후 갱신되는 값은 다를 수 있음(간단 처리)
    db.commit()
    db.refresh(msg)
    return msg


@router.get("/rooms/{chat_room_id}/messages", response_model=list[ChatMessageOut])
def list_messages(
    chat_room_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    room = db.get(ChatRoom, chat_room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Chat room not found")
    if user.id not in (room.company_id, room.student_id):
        raise HTTPException(status_code=403, detail="Not a participant")

    msgs = (
        db.query(ChatMessage)
        .filter(ChatMessage.chat_room_id == chat_room_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    return msgs


@router.put("/rooms/{chat_room_id}/read")
def mark_read(
    chat_room_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    room = db.get(ChatRoom, chat_room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Chat room not found")
    if user.id not in (room.company_id, room.student_id):
        raise HTTPException(status_code=403, detail="Not a participant")

    rs = (
        db.query(ChatReadStatus)
        .filter(ChatReadStatus.user_id == user.id, ChatReadStatus.chat_room_id == chat_room_id)
        .first()
    )
    if not rs:
        rs = ChatReadStatus(user_id=user.id, chat_room_id=chat_room_id)
        db.add(rs)

    db.commit()
    return {"ok": True}
