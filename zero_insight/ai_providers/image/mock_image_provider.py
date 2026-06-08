from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from zero_insight.ai_providers.base import ImageProvider


class MockImageProvider(ImageProvider):
    name = "mock"

    def generate_image(
        self,
        prompt: str,
        width: int,
        height: int,
        output_path: Path,
        negative_prompt: str | None = None,
    ) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image = Image.new("RGB", (width, height), (17, 24, 39))
        draw = ImageDraw.Draw(image, "RGBA")
        for y in range(height):
            ratio = y / max(1, height - 1)
            color = (
                int(17 * (1 - ratio) + 37 * ratio),
                int(24 * (1 - ratio) + 99 * ratio),
                int(39 * (1 - ratio) + 235 * ratio),
            )
            draw.line([(0, y), (width, y)], fill=color + (255,))
        draw.ellipse((int(width * 0.55), int(height * 0.08), int(width * 1.25), int(height * 0.45)), fill=(255, 255, 255, 28))
        image.save(output_path, format="PNG")
        return output_path
