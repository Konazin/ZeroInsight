from __future__ import annotations

import os

from zero_insight.ai_providers.base import OpenAICompatibleVisionProvider
from zero_insight.ai_providers.config import ProviderConfig


class CustomVisionProvider(OpenAICompatibleVisionProvider):
    def __init__(self, config: ProviderConfig) -> None:
        config.api_key_value = config.api_key_value or os.getenv("CUSTOM_TEXT_API_KEY") or None
        config.base_url = config.base_url or os.getenv("CUSTOM_TEXT_BASE_URL") or None
        config.endpoint = config.endpoint or os.getenv("CUSTOM_TEXT_ENDPOINT") or None
        config.model = config.model or os.getenv("CUSTOM_TEXT_MODEL", "")
        super().__init__(config)
