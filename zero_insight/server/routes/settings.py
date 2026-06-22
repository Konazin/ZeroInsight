from __future__ import annotations

import logging
from dataclasses import asdict, fields
from typing import Any

from fastapi import APIRouter, HTTPException

from zero_insight.config import Settings
from zero_insight.services import SettingsService

router = APIRouter(tags=["settings"])
logger = logging.getLogger(__name__)

_SECRET_KEYS = {"groq_api_key", "openai_api_key", "custom_text_api_key", "custom_image_api_key"}

_INT_FIELDS = {f.name for f in fields(Settings) if f.type in ("int", int)}


def _public_settings(settings: Settings) -> dict[str, Any]:
    data = asdict(settings)
    for key in _SECRET_KEYS:
        if data.get(key):
            data[key] = "****"
    return data


def _cast_value(key: str, value: Any) -> Any:
    if key in _INT_FIELDS:
        try:
            return int(value)
        except (ValueError, TypeError):
            raise HTTPException(status_code=422, detail=f"Campo '{key}' deve ser um número inteiro.")
    return value


@router.get("/settings")
def get_settings() -> dict[str, Any]:
    try:
        settings = Settings.from_env()
        return _public_settings(settings)
    except Exception as exc:
        logger.exception("Falha ao carregar configurações")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/settings")
def update_settings(values: dict[str, Any]) -> dict[str, Any]:
    try:
        service = SettingsService()
        settings = service.load()
        for key, value in values.items():
            if value == "****":
                continue
            if not hasattr(settings, key):
                continue
            setattr(settings, key, _cast_value(key, value))
        service.save(settings)
        return _public_settings(settings)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Falha ao salvar configurações")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

