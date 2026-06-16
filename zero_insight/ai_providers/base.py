from __future__ import annotations

import base64
import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import httpx

from zero_insight.ai_providers.config import ProviderConfig


class ProviderError(RuntimeError):
    pass


def resolve_api_key(config: ProviderConfig) -> str:
    if config.api_key_value:
        return config.api_key_value
    if config.api_key_env:
        return os.getenv(config.api_key_env, "")
    return ""


class TextProvider(ABC):
    name = "base"

    @abstractmethod
    def generate_text(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.4,
    ) -> str:
        raise NotImplementedError

    def generate_json(
        self,
        prompt: str,
        schema_hint: dict[str, Any] | None = None,
        system_prompt: str | None = None,
    ) -> dict[str, Any]:
        text = self.generate_text(prompt, system_prompt=system_prompt)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")
            if start >= 0 and end > start:
                return json.loads(text[start : end + 1])
            raise ProviderError("Provider retornou JSON invalido.")


class ImageProvider(ABC):
    name = "base"

    @abstractmethod
    def generate_image(
        self,
        prompt: str,
        width: int,
        height: int,
        output_path: Path,
        negative_prompt: str | None = None,
    ) -> Path:
        raise NotImplementedError


class VisionProvider(ABC):
    name = "base"

    @abstractmethod
    def analyze_image(self, image_path: Path, prompt: str) -> str:
        raise NotImplementedError


class OpenAICompatibleTextProvider(TextProvider):
    def __init__(self, config: ProviderConfig) -> None:
        self.config = config
        self.name = config.provider_name

    def generate_text(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.4,
    ) -> str:
        api_key = resolve_api_key(self.config)
        if not api_key:
            raise ProviderError("Provider configurado, mas API key nao foi encontrada.")
        endpoint = self.config.endpoint or self._endpoint("/chat/completions")
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        headers.update(self.config.extra_headers)
        if endpoint.rstrip("/").endswith("/responses"):
            return self._generate_responses(endpoint, headers, prompt, system_prompt, temperature)
        res = httpx.post(
            endpoint,
            headers=headers,
            json={
                "model": self.config.model,
                "messages": messages,
                "temperature": temperature,
                **self.config.extra_params,
            },
            timeout=90,
        )
        if not res.is_success:
            raise ProviderError(f"Provider texto retornou HTTP {res.status_code}: {res.text[:200]}")
        try:
            return res.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError("Formato de resposta de texto nao compativel com OpenAI chat/completions.") from exc

    def _generate_responses(
        self,
        endpoint: str,
        headers: dict[str, str],
        prompt: str,
        system_prompt: str | None,
        temperature: float,
    ) -> str:
        input_messages = []
        if system_prompt:
            input_messages.append({"role": "system", "content": system_prompt})
        input_messages.append({"role": "user", "content": prompt})
        res = httpx.post(
            endpoint,
            headers=headers,
            json={
                "model": self.config.model,
                "input": input_messages,
                "temperature": temperature,
                **self.config.extra_params,
            },
            timeout=90,
        )
        if not res.is_success:
            raise ProviderError(f"Provider texto retornou HTTP {res.status_code}: {res.text[:200]}")
        data = res.json()
        if data.get("output_text"):
            return str(data["output_text"])
        chunks: list[str] = []
        for item in data.get("output", []):
            for content in item.get("content", []):
                if content.get("text"):
                    chunks.append(str(content["text"]))
        if chunks:
            return "\n".join(chunks)
        raise ProviderError("Formato de resposta de texto nao compativel com OpenAI responses.")

    def _endpoint(self, suffix: str) -> str:
        if not self.config.base_url:
            raise ProviderError("Provider configurado, mas base URL/endpoint nao foi informado.")
        return self.config.base_url.rstrip("/") + suffix


class OpenAICompatibleImageProvider(ImageProvider):
    def __init__(self, config: ProviderConfig) -> None:
        self.config = config
        self.name = config.provider_name

    def generate_image(
        self,
        prompt: str,
        width: int,
        height: int,
        output_path: Path,
        negative_prompt: str | None = None,
    ) -> Path:
        api_key = resolve_api_key(self.config)
        if not api_key:
            raise ProviderError("Provider configurado, mas API key nao foi encontrada.")
        endpoint = self.config.endpoint or self._endpoint("/images/generations")
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        headers.update(self.config.extra_headers)
        res = httpx.post(
            endpoint,
            headers=headers,
            json={
                "model": self.config.model,
                "prompt": prompt,
                "size": f"{width}x{height}",
                **self.config.extra_params,
            },
            timeout=120,
        )
        if not res.is_success:
            raise ProviderError(f"Provider imagem retornou HTTP {res.status_code}: {res.text[:200]}")
        data = res.json()["data"][0]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if data.get("b64_json"):
            output_path.write_bytes(base64.b64decode(data["b64_json"]))
            return output_path
        if data.get("url"):
            image = httpx.get(data["url"], timeout=120)
            image.raise_for_status()
            output_path.write_bytes(image.content)
            return output_path
        raise ProviderError("Formato de resposta de imagem nao compativel: esperado b64_json ou url.")

    def _endpoint(self, suffix: str) -> str:
        if not self.config.base_url:
            raise ProviderError("Provider configurado, mas base URL/endpoint nao foi informado.")
        return self.config.base_url.rstrip("/") + suffix


class OpenAICompatibleVisionProvider(VisionProvider):
    def __init__(self, config: ProviderConfig) -> None:
        self.config = config
        self.name = config.provider_name

    def analyze_image(self, image_path: Path, prompt: str) -> str:
        api_key = resolve_api_key(self.config)
        if not api_key:
            raise ProviderError("Provider configurado, mas API key nao foi encontrada.")
        b64 = base64.b64encode(image_path.read_bytes()).decode("ascii")
        endpoint = self.config.endpoint or self._endpoint("/chat/completions")
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        headers.update(self.config.extra_headers)
        res = httpx.post(
            endpoint,
            headers=headers,
            json={
                "model": self.config.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                        ],
                    }
                ],
                **self.config.extra_params,
            },
            timeout=120,
        )
        if not res.is_success:
            raise ProviderError(f"Provider visao retornou HTTP {res.status_code}: {res.text[:200]}")
        return res.json()["choices"][0]["message"]["content"]

    def _endpoint(self, suffix: str) -> str:
        if not self.config.base_url:
            raise ProviderError("Provider configurado, mas base URL/endpoint nao foi informado.")
        return self.config.base_url.rstrip("/") + suffix
