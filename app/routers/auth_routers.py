from fastapi import APIRouter, Depends, HTTPException  # 라우터/의존성/예외
from sqlalchemy.ext.asyncio import AsyncSession  # 비동기 세션
from sqlalchemy import or_, select  # SQLAlchemy 조건/조회

from ..deps import get_async_db, create_access_token  # DB 의존성/JWT 생성
from ..auth import hash_password, verify_password  # 비밀번호 해시/검증
from ..models import User  # 사용자 모델
from ..schemas import SignupRequest, LoginRequest, TokenResponse, UserOut  # 요청/응답 스키마

router = APIRouter(prefix="/auth", tags=["auth"])  # /auth 라우터


@router.post("/signup", response_model=UserOut)  # 회원가입 엔드포인트
async def signup(  # 회원가입 핸들러
    payload: SignupRequest,  # 요청 바디
    db: AsyncSession = Depends(get_async_db),  # DB 세션
):
    if not payload.email and not payload.phone:  # 이메일/전화 모두 없으면
        raise HTTPException(status_code=422, detail="email or phone required")  # 유효성 오류

    conditions = []  # 중복 체크 조건 목록
    if payload.email:  # 이메일 제공 시
        conditions.append(User.email == payload.email)  # 이메일 중복 조건
    if payload.phone:  # 전화 제공 시
        conditions.append(User.phone == payload.phone)  # 전화 중복 조건

    if conditions:  # 조건이 있으면
        result = await db.execute(  # 조회 실행
            select(User).where(or_(*conditions))  # OR 조건
        )
        exists = result.scalar_one_or_none()  # 단일 사용자
        if exists:  # 이미 존재하면
            raise HTTPException(status_code=409, detail="email/phone already exists")  # 중복 오류

    user = User(  # 사용자 객체 생성
        email=payload.email,  # 이메일
        phone=payload.phone,  # 전화번호
        password_hash=hash_password(payload.password),  # 비밀번호 해시
        role=payload.role,  # 역할
        is_active=True,  # 활성화
    )
    db.add(user)  # 세션 추가
    await db.commit()  # 커밋
    await db.refresh(user)  # DB 반영값 갱신

    return user  # 사용자 반환


@router.post("/login", response_model=TokenResponse)  # 로그인 엔드포인트
async def login(  # 로그인 핸들러
    payload: LoginRequest,  # 요청 바디
    db: AsyncSession = Depends(get_async_db),  # DB 세션
):
    if not payload.email and not payload.phone:  # 이메일/전화 모두 없으면
        raise HTTPException(status_code=422, detail="email or phone required")  # 유효성 오류

    if payload.email:  # 이메일 로그인
        stmt = select(User).where(User.email == payload.email)  # 이메일 조건
    else:  # 전화 로그인
        stmt = select(User).where(User.phone == payload.phone)  # 전화 조건

    result = await db.execute(stmt)  # 조회 실행
    user = result.scalar_one_or_none()  # 단일 사용자

    if not user or not user.is_active:  # 사용자 없거나 비활성
        raise HTTPException(status_code=401, detail="Invalid credentials")  # 인증 실패

    if not verify_password(payload.password, user.password_hash):  # 비밀번호 검증
        raise HTTPException(status_code=401, detail="Invalid credentials")  # 인증 실패

    token = create_access_token(user.id)  # JWT 발급
    return TokenResponse(access_token=token)  # 토큰 응답
