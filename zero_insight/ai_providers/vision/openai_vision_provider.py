from zero_insight.ai_providers.base import OpenAICompatibleVisionProvider
from zero_insight.ai_providers.config import ProviderConfig


class OpenAIVisionProvider(OpenAICompatibleVisionProvider):
    def __init__(self, config: ProviderConfig) -> None:
        config.api_key_env = config.api_key_env or "OPENAI_API_KEY"
        config.base_url = config.base_url or "https://api.openai.com/v1"
        config.model = config.model or "gpt-5.5"
        super().__init__(config)
