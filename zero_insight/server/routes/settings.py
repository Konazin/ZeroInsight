from __future__ import annotations

import logging
import copy
from dataclasses import asdict, fields
from typing import Any

from fastapi import APIRouter, HTTPException

from zero_insight.config import Settings
from zero_insight.server.security import GENERIC_ERROR_DETAIL
from zero_insight.services import SettingsService

router = APIRouter(tags=["settings"])
logger = logging.getLogger(__name__)

_SECRET_KEYS = {"groq_api_key", "openai_api_key", "custom_text_api_key", "custom_image_api_key"}

_INT_FIELDS = {f.name for f in fields(Settings) if f.type in ("int", int)}


def _mask_nested_secrets(value: Any) -> Any:
    masked = copy.deepcopy(value)
    if isinstance(masked, dict):
        for key, item in list(masked.items()):
            if key in _SECRET_KEYS or key == "api_key_value":
                if item:
                    masked[key] = "****"
            else:
                masked[key] = _mask_nested_secrets(item)
    elif isinstance(masked, list):
        masked = [_mask_nested_secrets(item) for item in masked]
    return masked


def _restore_masked_values(value: Any, current: Any) -> Any:
    if value == "****":
        return current
    if isinstance(value, dict):
        current_dict = current if isinstance(current, dict) else {}
        return {
            key: _restore_masked_values(item, current_dict.get(key))
            for key, item in value.items()
        }
    if isinstance(value, list):
        current_list = current if isinstance(current, list) else []
        return [
            _restore_masked_values(item, current_list[index] if index < len(current_list) else None)
            for index, item in enumerate(value)
        ]
    return value


def _public_settings(settings: Settings) -> dict[str, Any]:
    return _mask_nested_secrets(asdict(settings))


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
        raise HTTPException(status_code=500, detail=GENERIC_ERROR_DETAIL) from exc


@router.post("/settings")
def update_settings(values: dict[str, Any]) -> dict[str, Any]:
    try:
        service = SettingsService()
        settings = service.load()
        for key, value in values.items():
            if not hasattr(settings, key):
                continue
            current = getattr(settings, key)
            restored = _restore_masked_values(value, current)
            setattr(settings, key, _cast_value(key, restored))
        service.save(settings)
        return _public_settings(settings)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Falha ao salvar configurações")
        raise HTTPException(status_code=500, detail=GENERIC_ERROR_DETAIL) from exc
