from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from zero_insight.brand.cache import load_brand_profile
from zero_insight.config import Settings
from zero_insight.content import StoryBrief, StorySlide
from zero_insight.image.prompt_builder import build_full_composition_prompt, build_prompt_package
from zero_insight.server.schemas import GeneratePostRequest, GenerateStoryRequest, ImagePreviewRequest
from zero_insight.services import PipelineService

router = APIRouter(tags=["generation"])
logger = logging.getLogger(__name__)


@router.post("/generate/post")
def generate_post(request: GeneratePostRequest) -> dict:
    try:
        ok, result = PipelineService(Settings.from_env()).run_blog(brand=request.brand)
        return {"ok": ok, "result": result}
    except Exception as exc:
        logger.exception("Falha na geração de post")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/generate/story")
def generate_story(request: GenerateStoryRequest) -> dict:
    if not request.topic.strip():
        raise HTTPException(status_code=422, detail="O campo 'topic' não pode ser vazio.")
    slides = max(1, min(request.slides, 10))
    try:
        settings = Settings.from_env()
        image_provider_name = request.ai_image_provider or settings.default_image_provider or settings.image_provider
        if image_provider_name == "openai" and not settings.openai_api_key:
            raise HTTPException(
                status_code=422,
                detail="OpenAI selecionada como provedor de imagem, mas OPENAI_API_KEY não está configurada. Vá em Configurações e adicione a chave.",
            )
        brief = StoryBrief(
            topic=request.topic.strip(),
            objective=request.objective,
            audience=request.audience,
            tone=request.tone,
            cta=request.cta,
            slides=slides,
            template=request.template or settings.story_default_template,
            source="dino" if request.from_dino else "api",
            brand_profile_id=request.brand_profile_id,
            ai_text_provider=request.ai_text_provider,
            ai_image_provider=request.ai_image_provider,
            company_summary=request.company_summary,
            custom_image_prompt=request.custom_image_prompt or None,
        )
        ok, manifest = PipelineService(settings).run_stories(brief, from_dino=request.from_dino)
        return {"ok": ok, "manifest": manifest}
    except Exception as exc:
        logger.exception("Falha na geração de story")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/generate/image-preview")
def image_preview(request: ImagePreviewRequest) -> dict:
    try:
        brand_profile = None
        if request.brand_profile_id:
            try:
                brand_profile = load_brand_profile(request.brand_profile_id)
            except Exception:
                logger.warning("BrandProfile '%s' não encontrado para prévia.", request.brand_profile_id)
        brief = StoryBrief(
            topic=request.topic,
            objective=request.objective,
            audience=request.audience,
            tone=request.tone,
            cta=request.cta,
            slides=3,
            template=request.format,
            brand_profile_id=request.brand_profile_id,
        )
        # Slide de exemplo com conteúdo representativo para o usuário ver a estrutura do prompt
        slide = StorySlide(
            order=1,
            hook=f"[Título do story sobre {request.topic}]",
            body="[Texto explicativo gerado pela IA com base no briefing e nos dados da empresa]",
            cta=request.cta,
            visual_idea=request.visual_idea,
            image_prompt=request.visual_idea,
        )
        # Retorna o prompt de composição completa — o mesmo que será enviado à OpenAI
        full_prompt = build_full_composition_prompt(brief, slide, brand_profile=brand_profile)
        package = build_prompt_package(brief, slide, brand_profile=brand_profile, destination=request.format)
        result = package.to_dict()
        result["prompt"] = full_prompt  # substitui o prompt de fundo pelo de composição completa
        return result
    except Exception as exc:
        logger.exception("Falha na prévia de imagem")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

