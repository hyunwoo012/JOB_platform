import os  # 환경 변수 접근
from datetime import datetime, timedelta, timezone  # 시간 계산
from typing import Optional  # Optional 타입

from fastapi import Depends, HTTPException, WebSocket  # FastAPI 의존성/예외/WS
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer  # 베어러 인증
from jose import JWTError, jwt  # JWT 인코딩/디코딩
from sqlalchemy.ext.asyncio import AsyncSession  # 비동기 세션
from sqlalchemy import select  # SQLAlchemy select

from .database import AsyncSessionLocal  # 세션 팩토리
from .models import User, UserRole  # 사용자 모델/역할

security = HTTPBearer(auto_error=False)  # Authorization 헤더 처리기

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change_me")  # JWT 비밀키
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")  # JWT 알고리즘
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080"))  # 만료(분)


# =========================
# DB Dependency (ASYNC)
# =========================
async def get_async_db():  # 요청 단위 DB 세션 제공
    async with AsyncSessionLocal() as session:  # 세션 컨텍스트
        yield session  # 세션 반환


# =========================
# JWT 생성 (기존 그대로)
# =========================
def create_access_token(user_id: int) -> str:  # 액세스 토큰 생성
    now = datetime.now(timezone.utc)  # 현재 시간(UTC)
    expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)  # 만료 시간

    payload = {  # JWT 페이로드
        "sub": str(user_id),  # 주체(사용자 ID)
        "iat": int(now.timestamp()),  # 발급 시각
        "exp": int(expire.timestamp()),  # 만료 시각
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)  # 토큰 반환


# =========================
# HTTP 인증 (ASYNC)
# =========================
async def get_current_user(  # 현재 사용자 확인
    creds: Optional[HTTPAuthorizationCredentials] = Depends(security),  # Authorization 헤더
    db: AsyncSession = Depends(get_async_db),  # DB 세션
) -> User:  # 반환 타입
    if creds is None:  # 토큰 미제공
        raise HTTPException(status_code=401, detail="Not authenticated")  # 인증 실패

    token = creds.credentials  # 실제 토큰 문자열
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])  # 토큰 디코딩
        user_id = int(payload.get("sub"))  # 사용자 ID 추출
    except (JWTError, ValueError):  # 디코딩 실패
        raise HTTPException(status_code=401, detail="Invalid token")  # 인증 실패

    result = await db.execute(select(User).where(User.id == user_id))  # 사용자 조회
    user = result.scalar_one_or_none()  # 단일 사용자

    if not user or not user.is_active:  # 사용자 없음/비활성
        raise HTTPException(status_code=401, detail="User not found or inactive")  # 인증 실패

    return user  # 사용자 반환


# =========================
# Role Guard (ASYNC)
# =========================
def require_role(*roles: UserRole):  # 역할 제한 데코레이터
    async def _role_guard(  # 실제 의존성 함수
        user: User = Depends(get_current_user),  # 현재 사용자
    ) -> User:  # 반환 타입
        if user.role not in roles:  # 허용 역할이 아니면
            raise HTTPException(status_code=403, detail="Forbidden (role)")  # 권한 실패
        return user  # 사용자 반환

    return _role_guard  # 의존성 반환


# =========================
# WebSocket 인증 (신규)
# =========================
async def get_current_user_ws(websocket: WebSocket) -> User:  # WS 사용자 인증
    """
    WebSocket용 JWT 인증
    - query param: ?token=xxx
    """  # 함수 설명
    token = websocket.query_params.get("token")  # 쿼리에서 토큰 추출
    if not token:  # 토큰 없으면
        await websocket.close(code=1008)  # 정책 위반 종료
        raise HTTPException(status_code=401, detail="Missing token")  # 인증 실패

    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])  # 토큰 디코딩
        user_id = int(payload.get("sub"))  # 사용자 ID 추출
    except (JWTError, ValueError):  # 디코딩 실패
        await websocket.close(code=1008)  # 정책 위반 종료
        raise HTTPException(status_code=401, detail="Invalid token")  # 인증 실패

    async with AsyncSessionLocal() as db:  # 임시 세션 생성
        result = await db.execute(select(User).where(User.id == user_id))  # 사용자 조회
        user = result.scalar_one_or_none()  # 단일 사용자

    if not user or not user.is_active:  # 사용자 없음/비활성
        await websocket.close(code=1008)  # 정책 위반 종료
        raise HTTPException(status_code=401, detail="User not found or inactive")  # 인증 실패

    return user  # 사용자 반환
