from pathlib import Path

from zero_insight.ai_providers.base import ProviderError, VisionProvider


class GeminiVisionProvider(VisionProvider):
    name = "gemini"

    def analyze_image(self, image_path: Path, prompt: str) -> str:
        raise ProviderError("Provider configurado, mas credenciais ou dependencias nao foram encontradas.")
