from datetime import datetime  # 시간
from typing import List, Optional  # 타입 힌트

from fastapi import APIRouter, Depends, HTTPException, Query  # 라우터/의존성/예외/쿼리
from sqlalchemy import select  # SQLAlchemy 조회
from sqlalchemy.ext.asyncio import AsyncSession  # 비동기 세션

from app.models import (  # 모델
    Application,  # 지원
    ApplicationStatus,  # 지원 상태
    JobPost,  # 공고
    ChatRoom,  # 채팅방
    UserRole,  # 사용자 역할
)
from app.schemas import (  # 스키마
    ApplicationCreate,  # 생성 요청
    ApplicationOut,  # 응답
)
from app.deps import get_current_user, get_async_db  # 의존성

router = APIRouter(  # 라우터 설정
    prefix="/applications",  # prefix
    tags=["Applications"],  # 태그
    dependencies=[],  # 전역 의존성 없음
)


# =========================
# 학생 → 채팅 요청 생성
# =========================
@router.post("", response_model=ApplicationOut)  # 지원 생성
async def create_application(  # 핸들러
        data: ApplicationCreate,  # 요청 바디
        db: AsyncSession = Depends(get_async_db),  # DB 세션
        me=Depends(get_current_user),  # 현재 사용자
):
    if me.role != UserRole.STUDENT:  # 학생만 가능
        raise HTTPException(status_code=403, detail="Only students can create applications")  # 권한 오류

    job_post = await db.get(JobPost, data.job_post_id)  # 공고 조회
    if not job_post:  # 없으면
        raise HTTPException(status_code=404, detail="Job post not found")  # 404

    existing = await db.execute(  # 기존 지원 조회
        select(Application).where(  # 조건
            Application.job_post_id == data.job_post_id,  # 공고 ID
            Application.student_id == me.id,  # 학생 ID
        )
    )
    existing_app = existing.scalar_one_or_none()  # 단일 지원

    if existing_app:  # 이미 있으면
        return existing_app  # 기존 지원 반환

    application = Application(  # 신규 지원 생성
        job_post_id=job_post.id,  # 공고 ID
        student_id=me.id,  # 학생 ID
        company_id=job_post.company_id,  # 회사 ID
        status=ApplicationStatus.REQUESTED,  # 상태
    )

    db.add(application)  # 세션 추가
    await db.commit()  # 커밋
    await db.refresh(application)  # DB 반영

    return application  # 지원 반환


# =========================
# 학생 → 내 Application 목록
# =========================
@router.get("/me", response_model=List[ApplicationOut])  # 내 지원 목록
async def list_my_applications(  # 핸들러
        db: AsyncSession = Depends(get_async_db),  # DB 세션
        me=Depends(get_current_user),  # 현재 사용자
):
    if me.role != UserRole.STUDENT:  # 학생만 가능
        raise HTTPException(status_code=403, detail="Only students can view this")  # 권한 오류

    result = await db.execute(  # 조회
        select(Application).where(Application.student_id == me.id)  # 내 지원
    )
    return result.scalars().all()  # 목록 반환


# =========================
# 회사 → 받은 Application 목록
# =========================
@router.get("", response_model=List[ApplicationOut])  # 회사 받은 목록
async def list_company_applications(  # 핸들러
        status: Optional[ApplicationStatus] = Query(None),  # 상태 필터
        db: AsyncSession = Depends(get_async_db),  # DB 세션
        me=Depends(get_current_user),  # 현재 사용자
):
    if me.role != UserRole.COMPANY:  # 회사만 가능
        raise HTTPException(status_code=403, detail="Only companies can view this")  # 권한 오류

    stmt = select(Application).where(Application.company_id == me.id)  # 회사 기준
    if status:  # 상태 필터
        stmt = stmt.where(Application.status == status)  # 상태 조건

    result = await db.execute(stmt)  # 조회 실행
    return result.scalars().all()  # 목록 반환


# =========================
# 회사 → Application 수락
# =========================
@router.post("/{application_id}/accept")  # 수락
async def accept_application(  # 핸들러
        application_id: int,  # 지원 ID
        db: AsyncSession = Depends(get_async_db),  # DB 세션
        me=Depends(get_current_user),  # 현재 사용자
):
    if me.role != UserRole.COMPANY:  # 회사만 가능
        raise HTTPException(status_code=403, detail="Only companies can accept applications")  # 권한 오류

    application = await db.get(Application, application_id)  # 지원 조회
    if not application:  # 없으면
        raise HTTPException(status_code=404, detail="Application not found")  # 404

    if application.company_id != me.id:  # 소유 확인
        raise HTTPException(status_code=403, detail="Not your application")  # 권한 오류

    if application.status != ApplicationStatus.REQUESTED:  # 이미 처리됨
        raise HTTPException(status_code=400, detail="Application already processed")  # 잘못된 요청

    application.status = ApplicationStatus.ACCEPTED  # 상태 변경
    application.responded_at = datetime.utcnow()  # 응답 시각

    chat_room = ChatRoom(  # 채팅방 생성
        application_id=application.id,  # 지원 ID
        job_post_id=application.job_post_id,  # 공고 ID
        company_id=application.company_id,  # 회사 ID
        student_id=application.student_id,  # 학생 ID
    )
    db.add(chat_room)  # 세션 추가

    try:
        await db.commit()  # 커밋
    except Exception:
        await db.rollback()  # 롤백
        raise HTTPException(status_code=400, detail="Chat room already exists")  # 중복 처리

    return {"message": "Application accepted"}  # 응답


# =========================
# 회사 → Application 거절
# =========================
@router.post("/{application_id}/reject")  # 거절
async def reject_application(  # 핸들러
        application_id: int,  # 지원 ID
        db: AsyncSession = Depends(get_async_db),  # DB 세션
        me=Depends(get_current_user),  # 현재 사용자
):
    if me.role != UserRole.COMPANY:  # 회사만 가능
        raise HTTPException(status_code=403, detail="Only companies can reject applications")  # 권한 오류

    application = await db.get(Application, application_id)  # 지원 조회
    if not application:  # 없으면
        raise HTTPException(status_code=404, detail="Application not found")  # 404

    if application.company_id != me.id:  # 소유 확인
        raise HTTPException(status_code=403, detail="Not your application")  # 권한 오류

    if application.status != ApplicationStatus.REQUESTED:  # 이미 처리됨
        raise HTTPException(status_code=400, detail="Application already processed")  # 잘못된 요청

    application.status = ApplicationStatus.REJECTED  # 상태 변경
    application.responded_at = datetime.utcnow()  # 응답 시각

    await db.commit()  # 커밋
    return {"message": "Application rejected"}  # 응답
