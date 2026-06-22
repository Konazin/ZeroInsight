from __future__ import annotations

import base64
import io
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
        # O SDK da OpenAI lê OPENAI_BASE_URL do ambiente mesmo sem passar base_url.
        # Se a variável estiver vazia no .env, ele monta URLs sem protocolo (httpcore.UnsupportedProtocol).
        # Solução: sempre passar base_url explicitamente — custom se configurado, padrão oficial caso contrário.
        base_url = self.base_url or "https://api.openai.com/v1"
        return OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=httpx.Timeout(None, connect=15.0),
            max_retries=0,
        )

    def generate_image(
        self,
        prompt: str,
        width: int,
        height: int,
        output_path: Path,
        negative_prompt: str | None = None,
        logo_path: str | None = None,
    ) -> Path:
        final_prompt = prompt if not negative_prompt else f"{prompt}\n\nAvoid: {negative_prompt}"
        size = self._supported_size(width, height)
        client = self._client()

        if logo_path and Path(logo_path).is_file():
            return self._generate_with_logo(client, final_prompt, size, output_path, Path(logo_path))

        return self._generate(client, final_prompt, size, output_path)

    def _generate(self, client: Any, prompt: str, size: str, output_path: Path) -> Path:
        kwargs: dict[str, Any] = {
            "model": self.config.model,
            "prompt": prompt,
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
        return self._save_response(response, prompt, size, output_path, logo_embedded=False)

    def _generate_with_logo(
        self, client: Any, prompt: str, size: str, output_path: Path, logo_path: Path
    ) -> Path:
        """Usa o endpoint /images/edits com canvas pré-montado contendo a logo.

        A OpenAI preserva áreas opacas (logo) e gera o restante (áreas transparentes),
        integrando a logo ao design em vez de sobrepô-la com PIL depois.
        """
        from PIL import Image as PILImage

        w, h = (map(int, size.split("x")) if "x" in size else (1024, 1536))

        canvas = PILImage.new("RGBA", (w, h), (0, 0, 0, 0))
        logo = PILImage.open(logo_path).convert("RGBA")
        logo.thumbnail((180, 100))
        margin = 64
        canvas.paste(logo, (margin, margin), logo)

        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
        buf.seek(0)

        kwargs: dict[str, Any] = {
            "model": self.config.model,
            "image": ("canvas.png", buf, "image/png"),
            "prompt": prompt,
            "size": size,
            "quality": self.quality,
            "n": 1,
        }
        if self.background:
            kwargs["background"] = self.background
        try:
            response = client.images.edit(**kwargs)
        except TypeError:
            kwargs.pop("background", None)
            buf.seek(0)
            response = client.images.edit(**kwargs)
        return self._save_response(response, prompt, size, output_path, logo_embedded=True)

    def _save_response(
        self, response: Any, prompt: str, size: str, output_path: Path, *, logo_embedded: bool
    ) -> Path:
        data = response.data[0]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if getattr(data, "b64_json", None):
            output_path.write_bytes(base64.b64decode(data.b64_json))
        elif getattr(data, "url", None):
            img = httpx.get(data.url, timeout=None)
            img.raise_for_status()
            output_path.write_bytes(img.content)
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
            "prompt_used": prompt,
            "logo_embedded": logo_embedded,
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
        compliance = (
            "Do not include content that implies guaranteed legal or financial results, "
            "misleading claims, sensationalist language, or content that violates platform policies."
        )
        return "\n\n".join(part for part in (prompt, compliance, negative_prompt) if part)
