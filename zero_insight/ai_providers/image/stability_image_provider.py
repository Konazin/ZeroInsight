from pathlib import Path

from zero_insight.ai_providers.base import ImageProvider, ProviderError


class StabilityImageProvider(ImageProvider):
    name = "stability"

    def generate_image(self, prompt: str, width: int, height: int, output_path: Path, negative_prompt: str | None = None) -> Path:
        raise ProviderError("Provider configurado, mas credenciais ou dependencias nao foram encontradas.")
