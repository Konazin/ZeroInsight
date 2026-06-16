from __future__ import annotations

from fastapi import APIRouter

from zero_insight.ai_providers import list_ai_providers, test_provider
from zero_insight.config import Settings
from zero_insight.server.schemas import ProviderTestRequest

router = APIRouter(tags=["providers"])


@router.get("/providers")
def providers() -> dict:
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


@router.post("/providers/test")
def test_provider_route(request: ProviderTestRequest) -> dict:
    ok, message = test_provider(request.kind, request.name)
    return {"ok": ok, "message": message}

