from __future__ import annotations

import logging
import sys
import threading
import time
import webbrowser
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from zero_insight.server.routes import brands, brave, generation, health, outputs, providers, prompts, settings
from zero_insight.server.security import GENERIC_ERROR_DETAIL, security_headers_middleware

logger = logging.getLogger(__name__)

# Em produção (app empacotado), desabilita a documentação interativa da API
# e o schema OpenAPI para reduzir a superfície de informação exposta.
_IS_FROZEN = getattr(sys, "frozen", False)

# Limite de corpo de requisição — protege contra payloads gigantes.
_MAX_REQUEST_BYTES = 20 * 1024 * 1024  # 20 MB

_DEFAULT_ORIGINS = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://127.0.0.1:5174",
    "http://localhost:5174",
]

# Set to True by run_server(open_browser=True) before uvicorn starts.
_open_browser_on_start: bool = False


def _build_cors_origins() -> list[str]:
    try:
        from zero_insight.config import Settings
        frontend_url = Settings.from_env().frontend_url.rstrip("/")
        origins = list(_DEFAULT_ORIGINS)
        if frontend_url and frontend_url not in origins:
            origins.append(frontend_url)
        return origins
    except Exception:
        return list(_DEFAULT_ORIGINS)


def _open_browser_delayed(url: str, delay: float = 0.8) -> None:
    time.sleep(delay)
    webbrowser.open(url)


@asynccontextmanager
async def _lifespan(app: FastAPI):
    if _open_browser_on_start:
        try:
            from zero_insight.config import Settings
            url = Settings.from_env().frontend_url
        except Exception:
            url = "http://127.0.0.1:5173"
        threading.Thread(target=_open_browser_delayed, args=(url,), daemon=True).start()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="ZeroInsight API",
        version="2.0.1",
        # Documentação interativa só em desenvolvimento.
        docs_url=None if _IS_FROZEN else "/api/docs",
        redoc_url=None if _IS_FROZEN else "/api/redoc",
        openapi_url=None if _IS_FROZEN else "/api/openapi.json",
        lifespan=_lifespan,
    )

    # Headers de segurança em todas as respostas.
    app.middleware("http")(security_headers_middleware)

    # Rejeita corpos de requisição maiores que o limite (via Content-Length).
    @app.middleware("http")
    async def _limit_body_size(request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > _MAX_REQUEST_BYTES:
                    return JSONResponse(
                        status_code=413,
                        content={"ok": False, "detail": "Requisição grande demais."},
                    )
            except ValueError:
                return JSONResponse(status_code=400, content={"ok": False, "detail": "Content-Length inválido."})
        return await call_next(request)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_build_cors_origins(),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        # Loga o erro completo no servidor, mas nunca expõe detalhes internos
        # (stack trace, caminhos, mensagens de exceção) ao cliente.
        logger.exception("Erro não tratado em %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"ok": False, "detail": GENERIC_ERROR_DETAIL})

    app.include_router(health.router, prefix="/api")
    app.include_router(settings.router, prefix="/api")
    app.include_router(providers.router, prefix="/api")
    app.include_router(brands.router, prefix="/api")
    app.include_router(generation.router, prefix="/api")
    app.include_router(outputs.router, prefix="/api")
    app.include_router(brave.router, prefix="/api")
    app.include_router(prompts.router, prefix="/api")

    # Serve the built React frontend — mounted LAST so all /api/* routes take priority.
    # Active only when the frontend/dist (or bundled frontend_dist) directory exists.
    _mount_frontend(app)

    return app


def _mount_frontend(app: FastAPI) -> None:
    """Mount the compiled React build as a static SPA at '/'."""
    import sys
    from pathlib import Path as _Path
    from fastapi.staticfiles import StaticFiles

    if getattr(sys, "frozen", False):
        # PyInstaller --onedir: frontend_dist is bundled next to the exe
        dist = _Path(sys.executable).parent / "frontend_dist"
    else:
        # Development / CI: check for a pre-built Vite output
        dist = _Path(__file__).resolve().parents[2] / "frontend" / "dist"

    if dist.is_dir():
        logger.info("Serving frontend from %s", dist)
        app.mount("/", StaticFiles(directory=str(dist), html=True), name="frontend")


app = create_app()


def run_server(open_browser: bool = False) -> None:
    global _open_browser_on_start
    _open_browser_on_start = open_browser

    import uvicorn

    from zero_insight.config import Settings

    srv = Settings.from_env()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    # Pass the app object directly (not a string) — string-based import breaks
    # in PyInstaller frozen mode where dynamic module discovery doesn't work.
    uvicorn.run(
        app,
        host=srv.backend_host,
        port=srv.backend_port,
        reload=False,
        log_level="info",
    )
