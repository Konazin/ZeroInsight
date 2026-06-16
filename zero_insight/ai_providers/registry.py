from __future__ import annotations

from zero_insight.ai_providers.base import ImageProvider, ProviderError, TextProvider, VisionProvider
from zero_insight.ai_providers.config import ProviderConfig
from zero_insight.ai_providers.image.custom_image_provider import CustomImageProvider
from zero_insight.ai_providers.image.local_image_provider import LocalImageProvider
from zero_insight.ai_providers.image.mock_image_provider import MockImageProvider
from zero_insight.ai_providers.image.openai_image_provider import OpenAIImageProvider
from zero_insight.ai_providers.image.replicate_image_provider import ReplicateImageProvider
from zero_insight.ai_providers.image.stability_image_provider import StabilityImageProvider
from zero_insight.ai_providers.text.anthropic_text_provider import AnthropicTextProvider
from zero_insight.ai_providers.text.custom_text_provider import CustomTextProvider
from zero_insight.ai_providers.text.gemini_text_provider import GeminiTextProvider
from zero_insight.ai_providers.text.groq_text_provider import GroqTextProvider
from zero_insight.ai_providers.text.mock_text_provider import MockTextProvider
from zero_insight.ai_providers.text.openai_text_provider import OpenAITextProvider
from zero_insight.ai_providers.vision.custom_vision_provider import CustomVisionProvider
from zero_insight.ai_providers.vision.gemini_vision_provider import GeminiVisionProvider
from zero_insight.ai_providers.vision.groq_vision_provider import GroqVisionProvider
from zero_insight.ai_providers.vision.mock_vision_provider import MockVisionProvider
from zero_insight.ai_providers.vision.openai_vision_provider import OpenAIVisionProvider


def list_ai_providers() -> dict[str, list[str]]:
    return {
        "text": ["mock", "custom", "openai", "anthropic", "gemini", "groq"],
        "image": ["local", "mock", "custom", "openai", "stability", "replicate"],
        "vision": ["mock", "custom", "openai", "gemini", "groq"],
    }


def create_text_provider(config: ProviderConfig | None = None) -> TextProvider:
    if not config or config.provider_name == "mock":
        return MockTextProvider()
    mapping = {
        "custom": CustomTextProvider,
        "openai": OpenAITextProvider,
        "groq": GroqTextProvider,
        "anthropic": lambda _config: AnthropicTextProvider(),
        "gemini": lambda _config: GeminiTextProvider(),
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
        "stability": lambda _config: StabilityImageProvider(),
        "replicate": lambda _config: ReplicateImageProvider(),
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
        "gemini": lambda _config: GeminiVisionProvider(),
    }
    factory = mapping.get(config.provider_name)
    if not factory:
        raise ProviderError(f"Provider de visao desconhecido: {config.provider_name}")
    return factory(config)  # type: ignore[misc]


def test_provider(kind: str, name: str) -> tuple[bool, str]:
    if kind == "text":
        provider = create_text_provider(ProviderConfig("text", name))
        try:
            provider.generate_text("Responda ok")
            return True, f"{kind}:{name} OK"
        except Exception as exc:
            return name == "mock", str(exc) if name != "mock" else "text:mock OK"
    if kind == "image":
        provider = create_image_provider(ProviderConfig("image", name))
        if name in {"local", "mock"}:
            return True, f"{provider.name} disponivel sem API"
        return True, "Provider requer configuracao externa."
    if kind == "vision":
        provider = create_vision_provider(ProviderConfig("vision", name))
        return True, f"{provider.name} disponivel" if name == "mock" else "Provider requer configuracao externa."
    return False, "Tipo invalido. Use text, image ou vision."
