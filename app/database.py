import os
from dotenv import load_dotenv

from sqlalchemy.ext.asyncio import (    # 비동기 관련 모듈 import
    create_async_engine,    # 비동기 DB 엔진 생성
    AsyncSession,           # 비동기 DB 세션
    async_sessionmaker,     # 세션 공장
)
from sqlalchemy.orm import DeclarativeBase      # ORM 모델의 부모 클래스

load_dotenv()   # .env 파일을 읽는

DATABASE_URL = os.getenv("DATABASE_URL")    # DATABASE_URL 로딩 및 검증
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set. Put it in .env")

#  async engine
engine = create_async_engine(       # Async Engine 생성   engine = DB와의 연결을 관리하는 "중앙 관리자"
    DATABASE_URL,
    pool_pre_ping=True,     # 퀴리 실행 전 DB가 살아있는지 체크 죽은 커넥션 자동 재연결
)

#  async session factory
AsyncSessionLocal = async_sessionmaker(     # 세션 공장 - 요청마다 사용할 DB 세션을 찍어주는 공장
    bind=engine,            # 위에서 만든 engine을 사용한다
    class_=AsyncSession,    # 비동기 AsyncSession
    expire_on_commit=False, # commit 후에도 객체를 유지
)


class Base(DeclarativeBase):    # 모든 ORM 모델의 공통 부모,
    pass
