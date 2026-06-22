from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from zero_insight.ai_providers import list_ai_providers, test_provider
from zero_insight.config import Settings
from zero_insight.server.schemas import ProviderTestRequest

router = APIRouter(tags=["providers"])
logger = logging.getLogger(__name__)


@router.get("/providers")
def providers() -> dict:
    try:
        settings = Settings.from_env()
        return {
            "available": list_ai_providers(),
            "active": {
                "text": settings.default_text_provider,
                "image": settings.default_image_provider,
                "vision": settings.default_vision_provider,
            },
            "openai": {
                "configured": bool(settings.openai_api_key),
                "text_model": settings.openai_text_model,
                "reasoning_model": settings.openai_reasoning_model,
                "image_model": settings.openai_image_model,
                "image_size": settings.openai_image_size,
            },
        }
    except Exception as exc:
        logger.exception("Falha ao carregar providers")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/providers/test")
def test_provider_route(request: ProviderTestRequest) -> dict:
    if not request.name.strip():
        raise HTTPException(status_code=422, detail="O nome do provider não pode ser vazio.")
    try:
        ok, message = test_provider(request.kind, request.name.strip())
        return {"ok": ok, "message": message}
    except Exception as exc:
        logger.warning("Erro ao testar provider %s:%s - %s", request.kind, request.name, exc)
        return {"ok": False, "message": str(exc)}

