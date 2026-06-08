from __future__ import annotations

import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from zero_insight.content import StoryBrief, StorySlide


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _wrap(text: str, width: int) -> str:
    return "\n".join(textwrap.wrap(text, width=width, break_long_words=False))


class StoryRenderer:
    def __init__(
        self,
        width: int,
        height: int,
        brand_name: str,
        primary_color: str,
        secondary_color: str,
        logo_path: str = "",
    ) -> None:
        self.width = width
        self.height = height
        self.brand_name = brand_name
        self.primary_color = primary_color
        self.secondary_color = secondary_color
        self.logo_path = logo_path

    def render(
        self,
        base_image_path: Path,
        slide: StorySlide,
        brief: StoryBrief,
        output_path: Path,
    ) -> Path:
        image = Image.open(base_image_path).convert("RGBA").resize((self.width, self.height))
        draw = ImageDraw.Draw(image, "RGBA")

        margin = 96
        top = 170
        bottom_safe = self.height - 210

        draw.rounded_rectangle(
            (margin - 28, top - 42, self.width - margin + 28, bottom_safe),
            radius=36,
            fill=(7, 13, 24, 105),
        )

        title_font = _font(72, bold=True)
        body_font = _font(42)
        cta_font = _font(42, bold=True)
        meta_font = _font(30)

        y = top
        draw.text((margin, y), _wrap(slide.hook, 18), font=title_font, fill=(255, 255, 255, 255))
        title_box = draw.multiline_textbbox((margin, y), _wrap(slide.hook, 18), font=title_font, spacing=10)
        y = title_box[3] + 52

        draw.text((margin, y), _wrap(slide.body, 32), font=body_font, fill=(239, 246, 255, 245), spacing=12)
        body_box = draw.multiline_textbbox((margin, y), _wrap(slide.body, 32), font=body_font, spacing=12)
        y = min(body_box[3] + 72, bottom_safe - 190)

        draw.rounded_rectangle(
            (margin, y, self.width - margin, y + 104),
            radius=22,
            fill=(255, 255, 255, 230),
        )
        draw.text((margin + 32, y + 26), _wrap(slide.cta, 28), font=cta_font, fill=(17, 24, 39, 255))

        draw.text((margin, self.height - 132), self.brand_name, font=meta_font, fill=(255, 255, 255, 230))
        if self.logo_path:
            try:
                logo = Image.open(self.logo_path).convert("RGBA")
                logo.thumbnail((150, 90))
                image.alpha_composite(logo, (margin, self.height - 238))
            except Exception:
                pass
        draw.text(
            (self.width - margin - 110, self.height - 132),
            f"{slide.order:02d}/{brief.slides:02d}",
            font=meta_font,
            fill=(255, 255, 255, 210),
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.convert("RGB").save(output_path, format="PNG")
        return output_path
