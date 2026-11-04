"""FastAPI application factory."""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.api import api_router
from app.ai_core.core.exceptions import AICoreError
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        description="Multi-tenant Educational Management SaaS (Phase 1: no AI)",
        version="1.0.0",
        openapi_url=f"{settings.api_v1_str}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        debug=settings.debug,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.backend_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # AI Core exception handler: converts AICoreError subclasses to proper HTTP responses
    @app.exception_handler(AICoreError)
    async def ai_core_exception_handler(request: Request, exc: AICoreError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message, "code": exc.code, "details": exc.details},
        )

    app.include_router(api_router, prefix=settings.api_v1_str)

    @app.get("/health", tags=["health"])
    async def health():
        return {"status": "ok", "service": settings.app_name, "env": settings.app_env}

    return app


app = create_app()
