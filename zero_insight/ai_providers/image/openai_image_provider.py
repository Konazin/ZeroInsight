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

    def _client(self) -> Any:
        api_key = self.config.api_key_value or os.getenv(self.config.api_key_env or "OPENAI_API_KEY", "")
        if not api_key:
            raise ProviderError("OpenAI configurada, mas OPENAI_API_KEY nao foi encontrada.")
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ProviderError("Dependencia oficial 'openai' nao instalada. Rode pip install -r requirements.txt.") from exc
        # O SDK da OpenAI lê OPENAI_BASE_URL do ambiente mesmo sem passar base_url.
        # Se a variável estiver vazia no .env, ele monta URLs sem protocolo (httpcore.UnsupportedProtocol).
        base_url = self.base_url or "https://api.openai.com/v1"
        return OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=httpx.Timeout(None, connect=15.0),
            max_retries=0,
        )

    # ── Interface pública ─────────────────────────────────────────────────────

    def generate_image(
        self,
        prompt: str,
        width: int,
        height: int,
        output_path: Path,
        negative_prompt: str | None = None,
        logo_path: str | None = None,
    ) -> Path:
        """Gera uma única imagem e salva em output_path."""
        final_prompt = prompt if not negative_prompt else f"{prompt}\n\nAvoid: {negative_prompt}"
        size = self._supported_size(width, height)
        client = self._client()
        response = self._api_call(client, final_prompt, size, n=1, logo_path=logo_path)
        return self._save_all(response, final_prompt, size, [output_path], logo_embedded=bool(logo_path and Path(logo_path).is_file()))[0]

    def generate_images_batch(
        self,
        prompt: str,
        width: int,
        height: int,
        output_dir: Path,
        count: int,
        prefix: str = "story",
        logo_path: str | None = None,
    ) -> list[Path]:
        """Gera `count` imagens em uma única chamada à API e salva em output_dir.

        Retorna a lista de paths na mesma ordem em que a API os enviou.
        """
        size = self._supported_size(width, height)
        client = self._client()
        output_dir.mkdir(parents=True, exist_ok=True)
        output_paths = [output_dir / f"{prefix}_{i:02d}_base.png" for i in range(1, count + 1)]
        response = self._api_call(client, prompt, size, n=count, logo_path=logo_path)
        return self._save_all(response, prompt, size, output_paths, logo_embedded=bool(logo_path and Path(logo_path).is_file()))

    # ── Internos ──────────────────────────────────────────────────────────────

    def _api_call(self, client: Any, prompt: str, size: str, n: int, logo_path: str | None) -> Any:
        """Escolhe entre /images/generate e /images/edit dependendo da logo."""
        if logo_path and Path(logo_path).is_file():
            return self._call_edit(client, prompt, size, n, Path(logo_path))
        return self._call_generate(client, prompt, size, n)

    def _call_generate(self, client: Any, prompt: str, size: str, n: int) -> Any:
        kwargs: dict[str, Any] = {
            "model": self.config.model,
            "prompt": prompt,
            "size": size,
            "quality": self.quality,
            "n": n,
        }
        if self.background:
            kwargs["background"] = self.background
        try:
            return client.images.generate(**kwargs)
        except TypeError:
            kwargs.pop("background", None)
            return client.images.generate(**kwargs)

    def _call_edit(self, client: Any, prompt: str, size: str, n: int, logo_path: Path) -> Any:
        """Canvas transparente com logo pré-posicionada — IA preserva a logo e gera o resto."""
        from PIL import Image as PILImage

        w, h = (map(int, size.split("x")) if "x" in size else (1024, 1536))
        canvas = PILImage.new("RGBA", (w, h), (0, 0, 0, 0))
        logo = PILImage.open(logo_path).convert("RGBA")
        logo.thumbnail((180, 100))
        canvas.paste(logo, (64, 64), logo)

        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
        buf.seek(0)

        kwargs: dict[str, Any] = {
            "model": self.config.model,
            "image": ("canvas.png", buf, "image/png"),
            "prompt": prompt,
            "size": size,
            "quality": self.quality,
            "n": n,
        }
        if self.background:
            kwargs["background"] = self.background
        try:
            return client.images.edit(**kwargs)
        except TypeError:
            kwargs.pop("background", None)
            buf.seek(0)
            return client.images.edit(**kwargs)

    def _save_all(
        self,
        response: Any,
        prompt: str,
        size: str,
        output_paths: list[Path],
        *,
        logo_embedded: bool,
    ) -> list[Path]:
        """Salva cada item de response.data no path correspondente."""
        saved: list[Path] = []
        for data, out in zip(response.data, output_paths):
            out.parent.mkdir(parents=True, exist_ok=True)
            if getattr(data, "b64_json", None):
                out.write_bytes(base64.b64decode(data.b64_json))
            elif getattr(data, "url", None):
                img = httpx.get(data.url, timeout=None)
                img.raise_for_status()
                out.write_bytes(img.content)
            else:
                raise ProviderError(f"Imagem sem base64 ou URL na resposta da OpenAI: {out.name}")
            saved.append(out)

        first = response.data[0] if response.data else None
        self.last_metadata = {
            "ai_image_provider": "openai",
            "ai_image_model": self.config.model,
            "ai_image_size": size,
            "ai_image_quality": self.quality,
            "image_format": self.image_format,
            "background": self.background,
            "revised_prompt": getattr(first, "revised_prompt", None) if first else None,
            "cost_estimate": None,
            "prompt_used": prompt,
            "logo_embedded": logo_embedded,
            "images_count": len(saved),
        }
        return saved

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
