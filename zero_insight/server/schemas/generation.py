from __future__ import annotations

from pydantic import BaseModel


class GeneratePostRequest(BaseModel):
    brand: str | None = None


class GenerateStoryRequest(BaseModel):
    topic: str = "RPV Federal"
    objective: str = "orientar com clareza"
    audience: str = "publico juridico"
    tone: str = "claro e responsavel"
    cta: str = "Fale com a Requisite"
    slides: int = 3
    template: str | None = None
    from_dino: bool = False
    brand_profile_id: str | None = None
    ai_text_provider: str | None = None
    ai_image_provider: str | None = None
    company_summary: str = ""
    custom_image_prompt: str | None = None


class ImagePreviewRequest(BaseModel):
    topic: str
    objective: str = "orientar com clareza"
    audience: str = "publico juridico"
    tone: str = "claro e responsavel"
    cta: str = "Fale com a Requisite"
    visual_idea: str = "fundo institucional limpo"
    format: str = "story"
    brand_profile_id: str | None = None

