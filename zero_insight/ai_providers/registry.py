from __future__ import annotations

from tempfile import TemporaryDirectory
from pathlib import Path

from zero_insight.ai_providers.base import (
    ImageProvider,
    ProviderError,
    TextProvider,
    VisionProvider,
    resolve_api_key,
)
from zero_insight.ai_providers.config import ProviderConfig
from zero_insight.ai_providers.image.custom_image_provider import CustomImageProvider
from zero_insight.ai_providers.image.local_image_provider import LocalImageProvider
from zero_insight.ai_providers.image.mock_image_provider import MockImageProvider
from zero_insight.ai_providers.image.openai_image_provider import OpenAIImageProvider
from zero_insight.ai_providers.text.custom_text_provider import CustomTextProvider
from zero_insight.ai_providers.text.groq_text_provider import GroqTextProvider
from zero_insight.ai_providers.text.mock_text_provider import MockTextProvider
from zero_insight.ai_providers.text.openai_text_provider import OpenAITextProvider
from zero_insight.ai_providers.vision.custom_vision_provider import CustomVisionProvider
from zero_insight.ai_providers.vision.groq_vision_provider import GroqVisionProvider
from zero_insight.ai_providers.vision.mock_vision_provider import MockVisionProvider
from zero_insight.ai_providers.vision.openai_vision_provider import OpenAIVisionProvider


def list_ai_providers() -> dict[str, list[str]]:
    return {
        "text": ["mock", "custom", "openai", "groq"],
        "image": ["local", "mock", "custom", "openai"],
        "vision": ["mock", "custom", "openai", "groq"],
    }


def create_text_provider(config: ProviderConfig | None = None) -> TextProvider:
    if not config or config.provider_name == "mock":
        return MockTextProvider()
    mapping = {
        "custom": CustomTextProvider,
        "openai": OpenAITextProvider,
        "groq": GroqTextProvider,
    }
    factory = mapping.get(config.provider_name)
    if not factory:
        raise ProviderError(f"Provider de texto desconhecido: {config.provider_name}")
    return factory(config)  # type: ignore[misc]


def create_image_provider(config: ProviderConfig | None = None) -> ImageProvider:
    if not config or config.provider_name == "mock":
        return MockImageProvider()
    mapping = {
        "local": LocalImageProvider,
        "custom": CustomImageProvider,
        "openai": OpenAIImageProvider,
    }
    factory = mapping.get(config.provider_name)
    if not factory:
        raise ProviderError(f"Provider de imagem desconhecido: {config.provider_name}")
    return factory(config)  # type: ignore[misc]


def create_vision_provider(config: ProviderConfig | None = None) -> VisionProvider:
    if not config or config.provider_name == "mock":
        return MockVisionProvider()
    mapping = {
        "custom": CustomVisionProvider,
        "openai": OpenAIVisionProvider,
        "groq": GroqVisionProvider,
    }
    factory = mapping.get(config.provider_name)
    if not factory:
        raise ProviderError(f"Provider de visao desconhecido: {config.provider_name}")
    return factory(config)  # type: ignore[misc]


def _remote_config_ready(config: ProviderConfig) -> tuple[bool, str]:
    if not resolve_api_key(config):
        return False, "API key não configurada."
    if config.provider_name != "openai" and not (config.endpoint or config.base_url):
        return False, "Base URL ou endpoint não configurado."
    if not config.model:
        return False, "Modelo não configurado."
    return True, "Configuração completa."


def test_provider(
    kind: str,
    name: str,
    config: ProviderConfig | None = None,
    prompt: str = "Responda apenas OK.",
) -> tuple[bool, str]:
    available = list_ai_providers()
    if kind not in available:
        return False, f"Tipo inválido: '{kind}'. Use text, image ou vision."
    if name not in available[kind]:
        return False, f"Provider {kind}:{name} não está implementado."

    config = config or ProviderConfig(kind, name)  # type: ignore[arg-type]
    try:
        if kind == "text":
            provider = create_text_provider(config)
            provider.generate_text(prompt)
            return True, f"text:{name} respondeu com sucesso."

        if kind == "image":
            provider = create_image_provider(config)
            if name in {"mock", "local"}:
                with TemporaryDirectory() as directory:
                    provider.generate_image(
                        "Teste visual local.",
                        64,
                        64,
                        Path(directory) / "provider_test.png",
                    )
                return True, f"image:{name} gerou uma imagem de teste."
            ok, message = _remote_config_ready(config)
            suffix = " Geração não executada para evitar cobrança." if ok else ""
            return ok, f"image:{name}: {message}{suffix}"

        provider = create_vision_provider(config)
        if name == "mock":
            with TemporaryDirectory() as directory:
                sample = Path(directory) / "sample.png"
                create_image_provider().generate_image("amostra", 16, 16, sample)
                provider.analyze_image(sample, prompt)
            return True, "vision:mock respondeu com sucesso."
        ok, message = _remote_config_ready(config)
        suffix = " Análise não executada para evitar cobrança." if ok else ""
        return ok, f"vision:{name}: {message}{suffix}"
    except Exception as exc:
        return False, str(exc)
