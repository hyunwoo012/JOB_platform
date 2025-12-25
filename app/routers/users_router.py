from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..deps import get_db, get_current_user, require_role
from ..models import User, UserRole, StudentProfile
from ..schemas import UserOut, StudentProfileUpsert, StudentProfileOut

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.get("/me/student-profile", response_model=StudentProfileOut)
def get_my_student_profile(
    user: User = Depends(require_role(UserRole.STUDENT)),
    db: Session = Depends(get_db),
):
    profile = db.get(StudentProfile, user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found")
    # skills를 리스트로 보이게
    profile.skills = profile.skills or []
    return profile


@router.put("/me/student-profile", response_model=StudentProfileOut)
def upsert_my_student_profile(
    payload: StudentProfileUpsert,
    user: User = Depends(require_role(UserRole.STUDENT)),
    db: Session = Depends(get_db),
):
    profile = db.get(StudentProfile, user.id)
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

    db.commit()
    db.refresh(profile)
    profile.skills = profile.skills or []
    return profile
