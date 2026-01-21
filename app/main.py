from fastapi import FastAPI  # FastAPI 앱 클래스
from .database import engine  # DB 엔진 로딩(환경 변수 검증용)
from .models import Base  # ORM 베이스(모델 등록 보장)

from .routers.auth_routers import router as auth_router  # 인증 라우터
from .routers.users_router import router as users_router  # 사용자/프로필 라우터
from .routers.posts_router import router as posts_router  # 공고 라우터
from .routers.chat_router import router as chat_router  # 채팅 REST 라우터
from .routers.chat_router import ws_router as chat_ws_router  # 채팅 WS 라우터
from .routers.applications_router import router as applications_router  # 지원(신청) 라우터
from .routers.chatbot_router import router as chatbot_router


def create_app() -> FastAPI:  # 앱 팩토리 함수
    app = FastAPI(title="Job Platform API")  # FastAPI 인스턴스 생성

    app.include_router(auth_router, prefix="/api")  # /api/auth 계열 라우트 등록
    app.include_router(users_router, prefix="/api")  # /api/users 계열 라우트 등록
    app.include_router(posts_router, prefix="/api")  # /api/job-posts 계열 라우트 등록
    app.include_router(chat_ws_router, prefix="/api")  # /api/ws 계열 라우트 등록
    app.include_router(applications_router, prefix="/api")  # /api/applications 계열 라우트 등록
    app.include_router(chat_router, prefix="/api")  # /api/chat 계열 라우트 등록
    app.include_router(chatbot_router, prefix="/api")

    @app.get("/health")  # 헬스체크 엔드포인트
    def health():  # 간단한 상태 확인 핸들러
        return {"ok": True}  # 서버 정상 응답

    return app  # 조립된 앱 반환


app = create_app()  # ASGI 서버에서 참조할 앱 객체
