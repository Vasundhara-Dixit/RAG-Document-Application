"""FastAPI main application entry point."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.routes import router as v1_router
from app.core.config import get_settings
from app.utils.logging import get_logger, setup_logging

logger = get_logger("main")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()
    setup_logging()

    app = FastAPI(
        title=settings.app.name,
        version=settings.app.version,
        description="Evaluation-driven RAG Document Q&A API",
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global standardized error handler per Rules.md §7
    @app.exception_handler(Exception)
    async def global_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.error(
            "Unhandled application exception",
            path=request.url.path,
            error=str(exc),
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred during request processing.",
                "detail": str(exc),
            },
        )

    # Mount v1 router
    app.include_router(v1_router)

    # Mount production frontend static files if built
    from pathlib import Path

    frontend_dist = Path("frontend/dist")
    if frontend_dist.exists():
        from fastapi.staticfiles import StaticFiles

        app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")
    else:
        @app.get("/")
        def root() -> dict[str, Any]:
            return {
                "app": settings.app.name,
                "version": settings.app.version,
                "docs_url": "/docs",
            }

    return app


app = create_app()

