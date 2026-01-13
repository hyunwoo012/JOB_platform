from fastapi import FastAPI
from .database import engine
from .models import Base

from .routers.auth_routers import router as auth_router
from .routers.users_router import router as users_router
from .routers.posts_router import router as posts_router
from .routers.chat_router import router as chat_router
from .routers.chat_router import ws_router as chat_ws_router
from .routers.applications_router import router as applications_router


def create_app() -> FastAPI:
    app = FastAPI(title="Job Platform API")         # fastapi 인스턴스 생성, title은 /docs에 표시됨

    app.include_router(auth_router, prefix="/api")  # 이 router 안에 정의된 모든 엔드포인트를 /api라는 공통 URL 아래 붙인다.
    app.include_router(users_router, prefix="/api") # include_router() users_router에 정의된 모든 route를 순회
    app.include_router(posts_router, prefix="/api") # 각 route의 path 앞에 /api를 붙임, 라이팅 테이블에 등록
    app.include_router(chat_ws_router, prefix="/api")
    app.include_router(chat_router, prefix="/api")
    app.include_router(applications_router, prefix="/api")

    @app.get("/health")         # 서버가 살아있는지 확인하기 위한 health check
    def health():
        return {"ok": True}

    return app      # 조립 완료된 앱 반환


app = create_app()  # 최종 실행 지점
