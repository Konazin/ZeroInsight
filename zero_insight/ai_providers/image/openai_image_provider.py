from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Any

import httpx

from zero_insight.ai_providers.base import ImageProvider, ProviderError
from zero_insight.ai_providers.config import ProviderConfig


class OpenAIImageProvider(ImageProvider):
    name = "openai"

    def __init__(self, config: ProviderConfig) -> None:
        self.config = config
        self.config.api_key_env = self.config.api_key_env or "OPENAI_API_KEY"
        self.config.model = self.config.model or os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-2")
        self.base_url = self.config.base_url or os.getenv("OPENAI_BASE_URL") or None
        self.size = str(self.config.extra_params.get("size") or os.getenv("OPENAI_IMAGE_SIZE", "1024x1536"))
        self.quality = str(self.config.extra_params.get("quality") or os.getenv("OPENAI_IMAGE_QUALITY", "medium"))
        self.image_format = str(self.config.extra_params.get("format") or os.getenv("OPENAI_IMAGE_FORMAT", "png"))
        self.background = str(self.config.extra_params.get("background") or os.getenv("OPENAI_IMAGE_BACKGROUND", "opaque"))
        self.last_metadata: dict[str, Any] = {}

    def _client(self):
        api_key = self.config.api_key_value or os.getenv(self.config.api_key_env or "OPENAI_API_KEY", "")
        if not api_key:
            raise ProviderError("OpenAI configurada, mas OPENAI_API_KEY nao foi encontrada.")
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ProviderError("Dependencia oficial 'openai' nao instalada. Rode pip install -r requirements.txt.") from exc
        kwargs: dict[str, Any] = {"api_key": api_key}
        if self.base_url:
            kwargs["base_url"] = self.base_url
        return OpenAI(**kwargs)

    def generate_image(
        self,
        prompt: str,
        width: int,
        height: int,
        output_path: Path,
        negative_prompt: str | None = None,
    ) -> Path:
        safe_prompt = self._safe_prompt(prompt, negative_prompt)
        size = self._supported_size(width, height)
        client = self._client()
        kwargs: dict[str, Any] = {
            "model": self.config.model,
            "prompt": safe_prompt,
            "size": size,
            "quality": self.quality,
            "n": 1,
        }
        if self.background:
            kwargs["background"] = self.background
        try:
            response = client.images.generate(**kwargs)
        except TypeError:
            kwargs.pop("background", None)
            response = client.images.generate(**kwargs)
        data = response.data[0]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if getattr(data, "b64_json", None):
            output_path.write_bytes(base64.b64decode(data.b64_json))
        elif getattr(data, "url", None):
            image = httpx.get(data.url, timeout=120)
            image.raise_for_status()
            output_path.write_bytes(image.content)
        else:
            raise ProviderError("Resposta da OpenAI Images sem base64 ou URL.")
        self.last_metadata = {
            "ai_image_provider": "openai",
            "ai_image_model": self.config.model,
            "ai_image_size": size,
            "ai_image_quality": self.quality,
            "image_format": self.image_format,
            "background": self.background,
            "revised_prompt": getattr(data, "revised_prompt", None),
            "cost_estimate": None,
            "prompt_used": safe_prompt,
        }
        return output_path

    def _supported_size(self, width: int, height: int) -> str:
        requested = self.size or f"{width}x{height}"
        supported = {"1024x1024", "1024x1536", "1536x1024", "auto"}
        if requested in supported:
            return requested
        if height > width:
            return "1024x1536"
        if width > height:
            return "1536x1024"
        return "1024x1024"

    @staticmethod
    def _safe_prompt(prompt: str, negative_prompt: str | None = None) -> str:
        blocked = (
            "Do not generate any text, letters, numbers, captions, fake logos, fake brand marks, "
            "watermarks, UI mockups, legal promises, financial guarantees, or sensationalist claims. "
            "The application will add final text, logo, CTA, and layout elements later."
        )
        return "\n\n".join(part for part in (prompt, blocked, negative_prompt) if part)
