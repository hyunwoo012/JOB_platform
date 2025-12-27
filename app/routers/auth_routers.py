from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, select

from ..deps import get_async_db, create_access_token
from ..auth import hash_password, verify_password
from ..models import User
from ..schemas import SignupRequest, LoginRequest, TokenResponse, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=UserOut)
async def signup(
    payload: SignupRequest,
    db: AsyncSession = Depends(get_async_db),
):
    if not payload.email and not payload.phone:
        raise HTTPException(status_code=422, detail="email or phone required")

    # 중복 체크
    conditions = []
    if payload.email:
        conditions.append(User.email == payload.email)
    if payload.phone:
        conditions.append(User.phone == payload.phone)

    if conditions:
        result = await db.execute(
            select(User).where(or_(*conditions))
        )
        exists = result.scalar_one_or_none()
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
    await db.commit()
    await db.refresh(user)

    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_async_db),
):
    if not payload.email and not payload.phone:
        raise HTTPException(status_code=422, detail="email or phone required")

    if payload.email:
        stmt = select(User).where(User.email == payload.email)
    else:
        stmt = select(User).where(User.phone == payload.phone)

    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(user.id)
    return TokenResponse(access_token=token)
