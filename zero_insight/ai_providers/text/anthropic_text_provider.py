from zero_insight.ai_providers.base import ProviderError, TextProvider


class AnthropicTextProvider(TextProvider):
    name = "anthropic"

    def generate_text(self, prompt: str, system_prompt: str | None = None, temperature: float = 0.4) -> str:
        raise ProviderError("Provider configurado, mas credenciais ou dependencias nao foram encontradas.")
