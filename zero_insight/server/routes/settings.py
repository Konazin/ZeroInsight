from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import APIRouter

from zero_insight.config import Settings
from zero_insight.services import SettingsService

router = APIRouter(tags=["settings"])


def _public_settings(settings: Settings) -> dict[str, Any]:
    data = asdict(settings)
    for key in ("groq_api_key", "openai_api_key", "custom_text_api_key", "custom_image_api_key"):
        if data.get(key):
            data[key] = "****"
    return data


@router.get("/settings")
def get_settings() -> dict[str, Any]:
    settings = Settings.from_env()
    return _public_settings(settings)


@router.post("/settings")
def update_settings(values: dict[str, Any]) -> dict[str, Any]:
    service = SettingsService()
    settings = service.load()
    for key, value in values.items():
        if value == "****":
            continue
        if hasattr(settings, key):
            setattr(settings, key, value)
    service.save(settings)
    return _public_settings(settings)

