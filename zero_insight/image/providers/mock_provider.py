from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from zero_insight.content import StoryBrief, StorySlide
from zero_insight.image.base import ImageProvider


def _hex_to_rgb(value: str, fallback: tuple[int, int, int]) -> tuple[int, int, int]:
    cleaned = value.strip().lstrip("#")
    if len(cleaned) != 6:
        return fallback
    try:
        return tuple(int(cleaned[i : i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return fallback


class MockImageProvider(ImageProvider):
    def __init__(
        self,
        width: int,
        height: int,
        primary_color: str,
        secondary_color: str,
    ) -> None:
        self.width = width
        self.height = height
        self.primary = _hex_to_rgb(primary_color, (17, 24, 39))
        self.secondary = _hex_to_rgb(secondary_color, (37, 99, 235))

    def generate_base_image(
        self,
        brief: StoryBrief,
        slide: StorySlide,
        output_path: Path,
    ) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image = Image.new("RGB", (self.width, self.height), self.primary)
        draw = ImageDraw.Draw(image, "RGBA")

        for y in range(self.height):
            ratio = y / max(1, self.height - 1)
            color = tuple(
                int(self.primary[i] * (1 - ratio) + self.secondary[i] * ratio)
                for i in range(3)
            )
            draw.line([(0, y), (self.width, y)], fill=color + (255,))

        draw.ellipse(
            (
                int(self.width * 0.55),
                int(self.height * 0.08),
                int(self.width * 1.25),
                int(self.height * 0.45),
            ),
            fill=(255, 255, 255, 28),
        )
        draw.rounded_rectangle(
            (
                int(self.width * 0.08),
                int(self.height * 0.62),
                int(self.width * 0.92),
                int(self.height * 0.82),
            ),
            radius=24,
            fill=(255, 255, 255, 30),
            outline=(255, 255, 255, 55),
            width=2,
        )
        image.save(output_path, format="PNG")
        return output_path
