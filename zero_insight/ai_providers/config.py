from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class ProviderConfig:
    provider_type: Literal["text", "image", "vision"]
    provider_name: str
    model: str = ""
    api_key_env: str | None = None
    api_key_value: str | None = None
    base_url: str | None = None
    endpoint: str | None = None
    extra_headers: dict[str, str] = field(default_factory=dict)
    extra_params: dict[str, object] = field(default_factory=dict)
    http_method: str = "POST"


def provider_config_from_settings(settings: Any, kind: str, name: str) -> ProviderConfig:
    """Build one provider configuration from the central Settings object."""
    providers = settings.providers or {}
    raw = providers.get(kind, {}).get(name, {}) if isinstance(providers, dict) else {}
    config = ProviderConfig(
        provider_type=kind,  # type: ignore[arg-type]
        provider_name=name,
        model=str(raw.get("model") or ""),
        api_key_env=raw.get("api_key_env"),
        api_key_value=raw.get("api_key_value"),
        base_url=raw.get("base_url"),
        endpoint=raw.get("endpoint"),
        extra_headers=dict(raw.get("extra_headers") or {}),
        extra_params=dict(raw.get("extra_params") or {}),
    )

    if name == "openai":
        config.api_key_value = config.api_key_value or settings.openai_api_key or None
        config.base_url = config.base_url or settings.openai_base_url or None
        if kind == "image":
            config.model = config.model or settings.openai_image_model
            config.extra_params.setdefault("size", settings.openai_image_size)
            config.extra_params.setdefault("quality", settings.openai_image_quality)
            config.extra_params.setdefault("format", settings.openai_image_format)
            config.extra_params.setdefault("background", settings.openai_image_background)
        elif kind == "text":
            config.model = config.model or settings.openai_text_model
        elif kind == "vision":
            config.model = config.model or settings.openai_vision_model
        return config

    if name == "groq":
        config.api_key_value = config.api_key_value or settings.groq_api_key or None
        config.endpoint = config.endpoint or settings.groq_endpoint or None
        config.model = config.model or (
            settings.groq_vision_model if kind == "vision" else settings.groq_model
        )
        return config

    if name == "custom":
        if kind in {"text", "vision"}:
            config.api_key_value = config.api_key_value or settings.custom_text_api_key or None
            config.base_url = config.base_url or settings.custom_text_base_url or None
            config.endpoint = config.endpoint or settings.custom_text_endpoint or None
            config.model = config.model or settings.custom_text_model
        elif kind == "image":
            config.api_key_value = config.api_key_value or settings.custom_image_api_key or None
            config.base_url = config.base_url or settings.custom_image_base_url or None
            config.endpoint = config.endpoint or settings.custom_image_endpoint or None
            config.model = config.model or settings.custom_image_model
        return config

    if name == "local" and kind == "image":
        config.model = config.model or settings.local_image_model_path
    return config
