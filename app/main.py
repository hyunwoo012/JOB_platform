from fastapi import FastAPI
from .database import engine
from .models import Base

from .routers.auth_routers import router as auth_router
from .routers.users_router import router as users_router
from .routers.posts_router import router as posts_router
from .routers.chat_router import router as chat_router


def create_app() -> FastAPI:
    app = FastAPI(title="Job Platform API")


    app.include_router(auth_router, prefix="/api")
    app.include_router(users_router, prefix="/api")
    app.include_router(posts_router, prefix="/api")
    app.include_router(chat_router, prefix="/api")

    @app.get("/health")
    def health():
        return {"ok": True}

    return app


app = create_app()
