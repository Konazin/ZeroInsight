from __future__ import annotations

from zero_insight.content import StoryBrief, StorySlide


def build_image_prompt(brief: StoryBrief, slide: StorySlide) -> str:
    return (
        f"{slide.image_prompt}. Tema: {brief.topic}. "
        "Nao incluir letras, palavras, logotipos falsos ou texto na imagem."
    )
