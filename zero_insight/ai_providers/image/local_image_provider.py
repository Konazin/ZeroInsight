from __future__ import annotations

import hashlib
from pathlib import Path

from PIL import Image, ImageDraw

from zero_insight.ai_providers.base import ImageProvider
from zero_insight.ai_providers.config import ProviderConfig


class LocalImageProvider(ImageProvider):
    name = "local"

    def __init__(self, config: ProviderConfig) -> None:
        self.config = config

    def generate_image(
        self,
        prompt: str,
        width: int,
        height: int,
        output_path: Path,
        negative_prompt: str | None = None,
    ) -> Path:
        if self.config.model:
            try:
                return self._generate_with_diffusers(prompt, width, height, output_path)
            except Exception:
                pass
        return self._generate_procedural(prompt, width, height, output_path)

    def _generate_with_diffusers(self, prompt: str, width: int, height: int, output_path: Path) -> Path:
        import torch
        from diffusers import StableDiffusionPipeline

        device = "cuda" if torch.cuda.is_available() else "cpu"
        dtype = torch.float16 if device == "cuda" else torch.float32
        pipe = StableDiffusionPipeline.from_pretrained(self.config.model, torch_dtype=dtype)
        pipe = pipe.to(device)
        image = pipe(
            prompt=prompt,
            negative_prompt="text, letters, watermark, fake logo, low quality",
            width=width,
            height=height,
            num_inference_steps=24,
        ).images[0]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path, format="PNG")
        return output_path

    @staticmethod
    def _generate_procedural(prompt: str, width: int, height: int, output_path: Path) -> Path:
        digest = hashlib.sha256(prompt.encode("utf-8", errors="ignore")).digest()
        primary = tuple(max(20, value) for value in digest[:3])
        secondary = tuple(max(40, value) for value in digest[3:6])
        accent = tuple(max(80, value) for value in digest[6:9])

        output_path.parent.mkdir(parents=True, exist_ok=True)
        image = Image.new("RGB", (width, height), primary)
        draw = ImageDraw.Draw(image, "RGBA")

        for y in range(height):
            ratio = y / max(1, height - 1)
            color = tuple(int(primary[i] * (1 - ratio) + secondary[i] * ratio) for i in range(3))
            draw.line([(0, y), (width, y)], fill=color + (255,))

        for index in range(7):
            seed = digest[9 + index]
            x = int((seed / 255) * width)
            y = int(((digest[index] / 255) * height))
            radius = int(width * (0.12 + (digest[index + 1] / 255) * 0.18))
            draw.ellipse(
                (x - radius, y - radius, x + radius, y + radius),
                fill=accent + (22 + index * 5,),
            )

        draw.rounded_rectangle(
            (int(width * 0.08), int(height * 0.58), int(width * 0.92), int(height * 0.84)),
            radius=28,
            fill=(255, 255, 255, 28),
            outline=(255, 255, 255, 58),
            width=2,
        )
        image.save(output_path, format="PNG")
        return output_path
