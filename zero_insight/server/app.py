from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from zero_insight.server.routes import brands, brave, generation, health, outputs, providers, settings


def create_app() -> FastAPI:
    app = FastAPI(title="ZeroInsight API", version="0.2.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router, prefix="/api")
    app.include_router(settings.router, prefix="/api")
    app.include_router(providers.router, prefix="/api")
    app.include_router(brands.router, prefix="/api")
    app.include_router(generation.router, prefix="/api")
    app.include_router(outputs.router, prefix="/api")
    app.include_router(brave.router, prefix="/api")
    return app


app = create_app()


def run_server() -> None:
    import uvicorn

    from zero_insight.config import Settings

    settings = Settings.from_env()
    uvicorn.run("zero_insight.server.app:app", host=settings.backend_host, port=settings.backend_port, reload=False)

