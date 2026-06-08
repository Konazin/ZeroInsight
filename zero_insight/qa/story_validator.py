from __future__ import annotations

from pathlib import Path

from PIL import Image

from zero_insight.content import StorySlide

DANGEROUS_TERMS = (
    "garantido",
    "100% aprovado",
    "sem risco",
    "dinheiro imediato garantido",
)


def validate_story_package(
    slides: list[StorySlide],
    image_paths: list[Path],
    width: int,
    height: int,
) -> dict[str, object]:
    errors: list[str] = []
    warnings: list[str] = []

    if len(slides) != len(image_paths):
        errors.append("Quantidade de slides e imagens nao confere.")

    for slide in slides:
        if not slide.hook.strip():
            errors.append(f"Story {slide.order}: hook ausente.")
        if not slide.body.strip():
            errors.append(f"Story {slide.order}: corpo ausente.")
        if not slide.cta.strip():
            errors.append(f"Story {slide.order}: CTA ausente.")
        text = " ".join([slide.hook, slide.body, slide.cta]).lower()
        for term in DANGEROUS_TERMS:
            if term in text:
                errors.append(f"Story {slide.order}: termo perigoso encontrado: {term}")

    for image_path in image_paths:
        if not image_path.exists():
            errors.append(f"Imagem nao encontrada: {image_path}")
            continue
        with Image.open(image_path) as image:
            if image.size != (width, height):
                errors.append(f"{image_path.name}: dimensao {image.size}, esperado {(width, height)}")

    return {"ok": not errors, "errors": errors, "warnings": warnings}
