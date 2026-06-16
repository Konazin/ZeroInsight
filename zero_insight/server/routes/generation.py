from __future__ import annotations

from fastapi import APIRouter

from zero_insight.config import Settings
from zero_insight.content import StoryBrief, StorySlide
from zero_insight.image.prompt_builder import build_prompt_package
from zero_insight.server.schemas import GeneratePostRequest, GenerateStoryRequest, ImagePreviewRequest
from zero_insight.services import PipelineService

router = APIRouter(tags=["generation"])


@router.post("/generate/post")
def generate_post(request: GeneratePostRequest) -> dict:
    ok, result = PipelineService(Settings.from_env()).run_blog(brand=request.brand)
    return {"ok": ok, "result": result}


@router.post("/generate/story")
def generate_story(request: GenerateStoryRequest) -> dict:
    settings = Settings.from_env()
    brief = StoryBrief(
        topic=request.topic,
        objective=request.objective,
        audience=request.audience,
        tone=request.tone,
        cta=request.cta,
        slides=max(1, request.slides),
        template=request.template or settings.story_default_template,
        source="dino" if request.from_dino else "api",
        brand_profile_id=request.brand_profile_id,
        ai_text_provider=request.ai_text_provider,
        ai_image_provider=request.ai_image_provider,
        company_summary=request.company_summary,
    )
    ok, manifest = PipelineService(settings).run_stories(brief, from_dino=request.from_dino)
    return {"ok": ok, "manifest": manifest}


@router.post("/generate/image-preview")
def image_preview(request: ImagePreviewRequest) -> dict:
    brief = StoryBrief(
        topic=request.topic,
        objective=request.objective,
        audience=request.audience,
        tone=request.tone,
        cta=request.cta,
        slides=1,
        template=request.format,
        brand_profile_id=request.brand_profile_id,
    )
    slide = StorySlide(1, "", "", request.cta, request.visual_idea, request.visual_idea)
    return build_prompt_package(brief, slide, destination=request.format).to_dict()

