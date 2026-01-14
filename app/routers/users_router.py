from fastapi import APIRouter, Depends, HTTPException  # 라우터/의존성/예외
from sqlalchemy.ext.asyncio import AsyncSession  # 비동기 세션
from sqlalchemy import select  # SQLAlchemy 조회

from ..deps import get_async_db, get_current_user, require_role  # 의존성/권한
from ..models import User, UserRole, StudentProfile  # 모델
from ..schemas import UserOut, StudentProfileUpsert, StudentProfileOut  # 스키마

router = APIRouter(prefix="/users", tags=["users"])  # /users 라우터


@router.get("/me", response_model=UserOut)  # 내 정보
async def me(  # 핸들러
    user: User = Depends(get_current_user),  # 현재 사용자
):
    return user  # 사용자 반환


@router.get("/me/student-profile", response_model=StudentProfileOut)  # 내 학생 프로필 조회
async def get_my_student_profile(  # 핸들러
    user: User = Depends(require_role(UserRole.STUDENT)),  # 학생만
    db: AsyncSession = Depends(get_async_db),  # DB 세션
):
    profile = await db.get(StudentProfile, user.id)  # 프로필 조회
    if not profile:  # 없으면
        raise HTTPException(status_code=404, detail="Student profile not found")  # 404

    profile.skills = profile.skills or []  # null 방어
    return profile  # 프로필 반환


@router.put("/me/student-profile", response_model=StudentProfileOut)  # 내 학생 프로필 생성/수정
async def upsert_my_student_profile(  # 핸들러
    payload: StudentProfileUpsert,  # 요청 바디
    user: User = Depends(require_role(UserRole.STUDENT)),  # 학생만
    db: AsyncSession = Depends(get_async_db),  # DB 세션
):
    profile = await db.get(StudentProfile, user.id)  # 기존 조회

    if not profile:  # 없으면 생성
        profile = StudentProfile(  # 새 프로필
            user_id=user.id,  # 사용자 ID
            name=payload.name,  # 이름
            school=payload.school,  # 학교
            major=payload.major,  # 전공
            skills=payload.skills,  # 기술
            available_time=payload.available_time,  # 가능 시간
        )
        db.add(profile)  # 세션 추가
    else:  # 있으면 갱신
        profile.name = payload.name  # 이름 갱신
        profile.school = payload.school  # 학교 갱신
        profile.major = payload.major  # 전공 갱신
        profile.skills = payload.skills  # 기술 갱신
        profile.available_time = payload.available_time  # 가능 시간 갱신

    await db.commit()  # 커밋
    await db.refresh(profile)  # 갱신 반영

    profile.skills = profile.skills or []  # null 방어
    return profile  # 프로필 반환
