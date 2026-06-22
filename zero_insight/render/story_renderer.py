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

        if brief.source == "manual_story_post":
            return self._render_visual_post(image, draw, slide, brief, output_path)

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

    def render_ai_output(
        self,
        base_image_path: Path,
        slide: StorySlide,
        brief: StoryBrief,
        output_path: Path,
        logo_embedded: bool = False,
    ) -> Path:
        """Salva imagem gerada pela IA adicionando apenas o contador de slide.

        Quando logo_embedded=True a logo já foi incluída pela IA via /images/edit —
        não sobrepõe nada, apenas adiciona o número do slide no canto inferior direito.
        Quando logo_embedded=False (geração simples sem logo), adiciona nome da marca
        em texto se não houver logo, ou faz o overlay da logo normalmente.
        """
        image = Image.open(base_image_path).convert("RGBA").resize((self.width, self.height))
        margin = 64
        meta_font = _font(28)
        draw = ImageDraw.Draw(image, "RGBA")

        if not logo_embedded:
            if self.logo_path and self.logo_path.strip():
                try:
                    logo = Image.open(self.logo_path).convert("RGBA")
                    logo.thumbnail((140, 80))
                    image.alpha_composite(logo, (margin, margin))
                except Exception:
                    pass
            else:
                brand_font = _font(28, bold=True)
                draw.text(
                    (margin, margin + 8),
                    self.brand_name,
                    font=brand_font,
                    fill=(255, 255, 255, 200),
                )

        counter = f"{slide.order:02d}/{brief.slides:02d}"
        draw.text(
            (self.width - margin - 90, self.height - margin - 36),
            counter,
            font=meta_font,
            fill=(255, 255, 255, 180),
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.convert("RGB").save(output_path, format="PNG")
        return output_path

    def _render_visual_post(
        self,
        image: Image.Image,
        draw: ImageDraw.ImageDraw,
        slide: StorySlide,
        brief: StoryBrief,
        output_path: Path,
    ) -> Path:
        margin = 86
        title_font = _font(78, bold=True)
        body_font = _font(38)
        cta_font = _font(38, bold=True)
        meta_font = _font(28)

        overlay = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay, "RGBA")
        overlay_draw.rectangle((0, 0, self.width, self.height), fill=(0, 0, 0, 58))
        overlay_draw.rounded_rectangle(
            (margin, 132, self.width - margin, self.height - 172),
            radius=34,
            fill=(7, 13, 24, 178),
            outline=(255, 255, 255, 42),
            width=2,
        )
        image.alpha_composite(overlay)
        draw = ImageDraw.Draw(image, "RGBA")

        if self.logo_path:
            try:
                logo = Image.open(self.logo_path).convert("RGBA")
                logo.thumbnail((180, 96))
                image.alpha_composite(logo, (margin + 42, 190))
            except Exception:
                pass

        y = 330
        hook = _wrap(slide.hook, 17)
        draw.text((margin + 42, y), hook, font=title_font, fill=(255, 255, 255, 255), spacing=8)
        title_box = draw.multiline_textbbox((margin + 42, y), hook, font=title_font, spacing=8)
        y = title_box[3] + 42

        body = _wrap(slide.body, 29)
        draw.text((margin + 42, y), body, font=body_font, fill=(236, 242, 248, 238), spacing=11)

        cta_y = self.height - 420
        draw.rounded_rectangle(
            (margin + 42, cta_y, self.width - margin - 42, cta_y + 104),
            radius=24,
            fill=(255, 255, 255, 238),
        )
        draw.text((margin + 78, cta_y + 28), _wrap(slide.cta, 27), font=cta_font, fill=(15, 23, 42, 255))

        draw.text((margin + 42, self.height - 252), self.brand_name, font=meta_font, fill=(255, 255, 255, 225))
        draw.text(
            (self.width - margin - 150, self.height - 252),
            f"{slide.order:02d}/{brief.slides:02d}",
            font=meta_font,
            fill=(255, 255, 255, 205),
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.convert("RGB").save(output_path, format="PNG")
        return output_path
