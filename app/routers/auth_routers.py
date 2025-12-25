from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_

from ..deps import get_db, create_access_token
from ..auth import hash_password, verify_password
from ..models import User
from ..schemas import SignupRequest, LoginRequest, TokenResponse, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=UserOut)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    if not payload.email and not payload.phone:
        raise HTTPException(status_code=422, detail="email or phone required")

    # 중복 체크
    q = []
    if payload.email:
        q.append(User.email == payload.email)
    if payload.phone:
        q.append(User.phone == payload.phone)

    if q:
        exists = db.query(User).filter(or_(*q)).first()
        if exists:
            raise HTTPException(status_code=409, detail="email/phone already exists")

    user = User(
        email=payload.email,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        role=payload.role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    if not payload.email and not payload.phone:
        raise HTTPException(status_code=422, detail="email or phone required")

    query = db.query(User)
    if payload.email:
        query = query.filter(User.email == payload.email)
    else:
        query = query.filter(User.phone == payload.phone)

    user = query.first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(user.id)
    return TokenResponse(access_token=token)
