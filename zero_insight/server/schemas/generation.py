from __future__ import annotations

from pydantic import BaseModel, Field

# Limites de tamanho para campos de texto livre — protegem contra payloads
# abusivos e mantêm os prompts enviados à IA dentro de limites razoáveis.
_SHORT = 200
_MEDIUM = 500
_LONG = 4000
_PROMPT = 20_000


class GeneratePostRequest(BaseModel):
    brand: str | None = Field(default=None, max_length=_SHORT)


class GenerateStoryRequest(BaseModel):
    topic: str = Field(default="RPV Federal", max_length=_MEDIUM)
    objective: str = Field(default="orientar com clareza", max_length=_MEDIUM)
    audience: str = Field(default="publico juridico", max_length=_MEDIUM)
    tone: str = Field(default="claro e responsavel", max_length=_MEDIUM)
    cta: str = Field(default="Fale com a Requisite", max_length=_SHORT)
    slides: int = Field(default=3, ge=1, le=10)
    template: str | None = Field(default=None, max_length=_SHORT)
    from_dino: bool = False
    brand_profile_id: str | None = Field(default=None, max_length=_SHORT)
    ai_text_provider: str | None = Field(default=None, max_length=_SHORT)
    ai_image_provider: str | None = Field(default=None, max_length=_SHORT)
    company_summary: str = Field(default="", max_length=_LONG)
    custom_image_prompt: str | None = Field(default=None, max_length=_PROMPT)
    image_style_instructions: str | None = Field(default=None, max_length=_PROMPT)


class ImagePreviewRequest(BaseModel):
    topic: str = Field(max_length=_MEDIUM)
    objective: str = Field(default="orientar com clareza", max_length=_MEDIUM)
    audience: str = Field(default="publico juridico", max_length=_MEDIUM)
    tone: str = Field(default="claro e responsavel", max_length=_MEDIUM)
    cta: str = Field(default="Fale com a Requisite", max_length=_SHORT)
    visual_idea: str = Field(default="fundo institucional limpo", max_length=_LONG)
    format: str = Field(default="story", max_length=_SHORT)
    brand_profile_id: str | None = Field(default=None, max_length=_SHORT)
