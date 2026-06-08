from pathlib import Path

from zero_insight.ai_providers.base import VisionProvider


class MockVisionProvider(VisionProvider):
    name = "mock"

    def analyze_image(self, image_path: Path, prompt: str) -> str:
        return f"Analise mock de {image_path.name}: imagem disponivel para revisao humana."
