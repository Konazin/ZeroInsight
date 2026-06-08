from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


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
