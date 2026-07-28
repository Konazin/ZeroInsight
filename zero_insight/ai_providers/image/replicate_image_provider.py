from pathlib import Path

from zero_insight.ai_providers.base import ImageProvider, ProviderError


class ReplicateImageProvider(ImageProvider):
    name = "replicate"

    def generate_image(
        self,
        prompt: str,
        width: int,
        height: int,
        output_path: Path,
        negative_prompt: str | None = None,
        logo_path: str | None = None,
    ) -> Path:
        raise ProviderError("Provider configurado, mas credenciais ou dependencias nao foram encontradas.")
