import os  # 환경 변수 접근
from dotenv import load_dotenv  # .env 로더

from sqlalchemy.ext.asyncio import (  # 비동기 SQLAlchemy 구성요소
    create_async_engine,  # 비동기 엔진 생성기
    AsyncSession,  # 비동기 세션 클래스
    async_sessionmaker,  # 비동기 세션 팩토리
)
from sqlalchemy.orm import DeclarativeBase  # ORM 베이스 클래스

load_dotenv()  # .env 파일에서 환경 변수 로드

DATABASE_URL = os.getenv("ASYNC_DATABASE_URL")  # 비동기 DB URL 읽기
if not DATABASE_URL:  # URL이 없으면
    raise RuntimeError("DATABASE_URL is not set. Put it in .env")  # 즉시 오류

engine = create_async_engine(  # 비동기 엔진 생성
    DATABASE_URL,  # DB 연결 문자열
    pool_pre_ping=True,  # 사용 전 커넥션 생존 확인
)

AsyncSessionLocal = async_sessionmaker(  # 요청 단위 세션 팩토리
    bind=engine,  # 엔진 연결
    class_=AsyncSession,  # 비동기 세션 타입
    expire_on_commit=False,  # 커밋 후 객체 유지
)


class Base(DeclarativeBase):  # 모든 모델의 공통 베이스
    pass  # 추가 동작 없음
