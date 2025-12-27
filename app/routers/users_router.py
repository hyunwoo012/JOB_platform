from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..deps import get_async_db, get_current_user, require_role
from ..models import User, UserRole, StudentProfile
from ..schemas import UserOut, StudentProfileUpsert, StudentProfileOut

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
async def me(
    user: User = Depends(get_current_user),
):
    return user


@router.get("/me/student-profile", response_model=StudentProfileOut)
async def get_my_student_profile(
    user: User = Depends(require_role(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_async_db),
):
    profile = await db.get(StudentProfile, user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found")

    profile.skills = profile.skills or []
    return profile


@router.put("/me/student-profile", response_model=StudentProfileOut)
async def upsert_my_student_profile(
    payload: StudentProfileUpsert,
    user: User = Depends(require_role(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_async_db),
):
    profile = await db.get(StudentProfile, user.id)

    if not profile:
        profile = StudentProfile(
            user_id=user.id,
            name=payload.name,
            school=payload.school,
            major=payload.major,
            skills=payload.skills,
            available_time=payload.available_time,
        )
        db.add(profile)
    else:
        profile.name = payload.name
        profile.school = payload.school
        profile.major = payload.major
        profile.skills = payload.skills
        profile.available_time = payload.available_time

    await db.commit()
    await db.refresh(profile)

    profile.skills = profile.skills or []
    return profile
