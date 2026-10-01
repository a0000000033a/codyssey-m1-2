from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.auth import require_owner
from .core.config import Settings
from .core.errors import ApiError, api_error_handler


def create_app(settings: Settings | None = None, dependencies=None, token_verifier=None) -> FastAPI:
    app = FastAPI(title="국내 주식 AI 분석 비서", version="0.1.0")
    app.state.settings = settings or Settings()
    app.state.dependencies = dependencies
    app.state.token_verifier = token_verifier
    app.add_exception_handler(ApiError, api_error_handler)
    app.add_middleware(CORSMiddleware, allow_origins=app.state.settings.allowed_origins,
                       allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                       allow_headers=["Authorization", "Content-Type"])

    @app.get("/health", tags=["상태"])
    def health():
        return {"status": "ok", "configured": bool(app.state.settings.allowed_user_uid)}

    @app.get("/api/me", tags=["인증"])
    def me(uid: str = Depends(require_owner)):
        return {"authenticated": True}

    return app


app = create_app()
