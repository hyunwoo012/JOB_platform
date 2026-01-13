from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models import (
    Application,
    ApplicationStatus,
    JobPost,
    ChatRoom,
)
from app.schemas import (
    ApplicationCreate,
    ApplicationOut,
)
from app.deps import get_current_user
from app.models import UserRole


router = APIRouter(
    prefix="/chat/applications",
    tags=["Applications"],
)


# =========================
# 학생 → 채팅 요청 생성
# =========================
@router.post("", response_model=ApplicationOut)
async def create_application(
    data: ApplicationCreate,
    db: AsyncSession = Depends(AsyncSessionLocal),
    me=Depends(get_current_user),
):
    if me.role != UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Only students can create applications")

    job_post = await db.get(JobPost, data.job_post_id)
    if not job_post:
        raise HTTPException(status_code=404, detail="Job post not found")

    application = Application(
        job_post_id=job_post.id,
        student_id=me.id,
        company_id=job_post.company_id,
        status=ApplicationStatus.REQUESTED,
    )

    db.add(application)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Already applied")

    await db.refresh(application)
    return application


# =========================
# 학생 → 내 Application 목록
# =========================
@router.get("/me", response_model=List[ApplicationOut])
async def list_my_applications(
    db: AsyncSession = Depends(AsyncSessionLocal),
    me=Depends(get_current_user),
):
    if me.role != UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Only students can view this")

    result = await db.execute(
        select(Application).where(Application.student_id == me.id)
    )
    return result.scalars().all()


# =========================
# 회사 → 받은 Application 목록
# =========================
@router.get("", response_model=List[ApplicationOut])
async def list_company_applications(
    status: Optional[ApplicationStatus] = Query(None),
    db: AsyncSession = Depends(AsyncSessionLocal),
    me=Depends(get_current_user),
):
    if me.role != UserRole.COMPANY:
        raise HTTPException(status_code=403, detail="Only companies can view this")

    stmt = select(Application).where(Application.company_id == me.id)
    if status:
        stmt = stmt.where(Application.status == status)

    result = await db.execute(stmt)
    return result.scalars().all()


# =========================
# 회사 → Application 수락
# =========================
@router.post("/{application_id}/accept")
async def accept_application(
    application_id: int,
    db: AsyncSession = Depends(AsyncSessionLocal),
    me=Depends(get_current_user),
):
    if me.role != UserRole.COMPANY:
        raise HTTPException(status_code=403, detail="Only companies can accept applications")

    application = await db.get(Application, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    if application.company_id != me.id:
        raise HTTPException(status_code=403, detail="Not your application")

    if application.status != ApplicationStatus.REQUESTED:
        raise HTTPException(status_code=400, detail="Application already processed")

    # 상태 변경
    application.status = ApplicationStatus.ACCEPTED
    application.responded_at = datetime.utcnow()

    # 채팅방 생성 (Application 기반)
    chat_room = ChatRoom(
        application_id=application.id,
        job_post_id=application.job_post_id,
        company_id=application.company_id,
        student_id=application.student_id,
    )
    db.add(chat_room)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Chat room already exists")

    return {"message": "Application accepted"}


# =========================
# 회사 → Application 거절
# =========================
@router.post("/{application_id}/reject")
async def reject_application(
    application_id: int,
    db: AsyncSession = Depends(AsyncSessionLocal),
    me=Depends(get_current_user),
):
    if me.role != UserRole.COMPANY:
        raise HTTPException(status_code=403, detail="Only companies can reject applications")

    application = await db.get(Application, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    if application.company_id != me.id:
        raise HTTPException(status_code=403, detail="Not your application")

    if application.status != ApplicationStatus.REQUESTED:
        raise HTTPException(status_code=400, detail="Application already processed")

    application.status = ApplicationStatus.REJECTED
    application.responded_at = datetime.utcnow()

    await db.commit()
    return {"message": "Application rejected"}
