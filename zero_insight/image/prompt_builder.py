from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from zero_insight.brand import BrandProfile
from zero_insight.content import StoryBrief, StorySlide


IMAGE_SYSTEM_INSTRUCTION = (
    "You are an expert art director and brand designer creating background visuals "
    "for institutional social media content. Generate only clean base imagery. "
    "Final text, logo, CTA, and UI elements will be added later by the application."
)


@dataclass
class ImagePromptPackage:
    prompt_type: str
    system_instruction: str
    prompt: str
    negative_instructions: list[str]
    destination: str
    safe_zone: dict[str, int]
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


NEGATIVE_INSTRUCTIONS = [
    "Do not include text.",
    "Do not include letters.",
    "Do not include numbers.",
    "Do not include fake logos.",
    "Do not include watermarks.",
    "Do not include fake brand marks.",
    "Do not include UI mockups unless explicitly requested.",
    "Do not imply guaranteed legal or financial results.",
    "Avoid distorted hands, faces, documents, seals, gavels, money, or flags unless specifically requested.",
]


def build_image_prompt(brief: StoryBrief, slide: StorySlide, brand_profile: BrandProfile | None = None) -> str:
    return build_story_background_prompt(brief, slide, brand_profile).prompt


def build_prompt_package(
    brief: StoryBrief,
    slide: StorySlide,
    brand_profile: BrandProfile | None = None,
    destination: str = "story",
) -> ImagePromptPackage:
    prompt_type = {
        "story": "story_background_prompt",
        "feed": "feed_post_background_prompt",
        "carousel": "carousel_slide_background_prompt",
        "metric": "metric_visual_prompt",
        "brand_asset": "brand_asset_prompt",
    }.get(destination, "story_background_prompt")
    return _build_package(prompt_type, brief, slide, brand_profile, destination)


def build_story_background_prompt(
    brief: StoryBrief,
    slide: StorySlide,
    brand_profile: BrandProfile | None = None,
) -> ImagePromptPackage:
    return _build_package("story_background_prompt", brief, slide, brand_profile, "story")


def build_feed_post_background_prompt(
    brief: StoryBrief,
    slide: StorySlide,
    brand_profile: BrandProfile | None = None,
) -> ImagePromptPackage:
    return _build_package("feed_post_background_prompt", brief, slide, brand_profile, "feed")


def build_carousel_slide_background_prompt(
    brief: StoryBrief,
    slide: StorySlide,
    brand_profile: BrandProfile | None = None,
) -> ImagePromptPackage:
    return _build_package("carousel_slide_background_prompt", brief, slide, brand_profile, "carousel")


def build_metric_visual_prompt(
    brief: StoryBrief,
    slide: StorySlide,
    brand_profile: BrandProfile | None = None,
) -> ImagePromptPackage:
    return _build_package("metric_visual_prompt", brief, slide, brand_profile, "metric")


def build_brand_asset_prompt(
    brief: StoryBrief,
    slide: StorySlide,
    brand_profile: BrandProfile | None = None,
) -> ImagePromptPackage:
    return _build_package("brand_asset_prompt", brief, slide, brand_profile, "brand_asset")


def _build_package(
    prompt_type: str,
    brief: StoryBrief,
    slide: StorySlide,
    brand_profile: BrandProfile | None,
    destination: str,
) -> ImagePromptPackage:
    brand_name = brand_profile.brand_name if brand_profile else "Brand not specified"
    tone = ", ".join(brand_profile.tone_of_voice) if brand_profile and brand_profile.tone_of_voice else brief.tone
    visual_style = ", ".join(brand_profile.visual_style) if brand_profile and brand_profile.visual_style else "modern, clean, institutional"
    colors = _colors(brand_profile)
    typography = "; ".join(brand_profile.typography_notes) if brand_profile and brand_profile.typography_notes else "Renderer will add typography later."
    layout_rules = _joined(brand_profile.layout_rules if brand_profile else [], "Clean hierarchy, center text safe zone, minimal clutter.")
    image_rules = _joined(brand_profile.image_style_rules if brand_profile else [], "Professional, calm, credible, high contrast.")
    format_rules = _format_rules(destination)
    prompt = f"""Create a {format_rules["label"]} institutional background image for social media.

Format:
- {format_rules["composition"]}
- Intended final export: {format_rules["export"]}.
- Leave safe empty space for text overlays.
- Keep top and bottom areas visually clean because platform UI may cover them.
- Main subject must not block the center text area.
- No text, letters, captions, fake logos, watermarks, or brand marks.

Brand:
{brand_name}

Brand tone:
{tone}

Visual style:
{visual_style}

Preferred colors:
{colors}

Typography notes, for renderer only:
{typography}

Layout rules:
{layout_rules}

Image style rules:
{image_rules}

Topic:
{brief.topic}

Objective:
{brief.objective}

Audience:
{brief.audience}

Visual idea:
{slide.visual_idea or slide.image_prompt}

Desired mood:
Trustworthy, modern, clean, institutional, professional, calm, credible.

Composition:
- Clean background.
- Strong visual hierarchy.
- High contrast.
- Room for headline and CTA overlay.
- Subtle depth.
- Minimal clutter.
- Realistic or semi-realistic style depending on BrandProfile.
- Avoid busy details behind expected text zones.

Output:
One clean background image suitable for final layout composition."""
    return ImagePromptPackage(
        prompt_type=prompt_type,
        system_instruction=IMAGE_SYSTEM_INSTRUCTION,
        prompt=prompt,
        negative_instructions=NEGATIVE_INSTRUCTIONS,
        destination=destination,
        safe_zone={"top": 240, "bottom": 280, "side": 72},
        metadata={
            "topic": brief.topic,
            "objective": brief.objective,
            "audience": brief.audience,
            "slide_order": slide.order,
            "brand_name": brand_name,
        },
    )


def _colors(brand_profile: BrandProfile | None) -> str:
    if not brand_profile or not brand_profile.color_palette:
        return "Use restrained institutional colors; avoid a one-note palette."
    return ", ".join(
        f"{color.get('name', 'color')} {color.get('hex', '')}".strip()
        for color in brand_profile.color_palette
    )


def _joined(values: list[str], fallback: str) -> str:
    return "; ".join(values) if values else fallback


def _format_rules(destination: str) -> dict[str, str]:
    if destination == "feed":
        return {"label": "square or portrait feed post", "composition": "Feed composition with generous overlay space", "export": "1080x1350 or 1080x1080"}
    if destination == "carousel":
        return {"label": "carousel slide", "composition": "Slide composition with consistent visual rhythm", "export": "1080x1350"}
    if destination == "metric":
        return {"label": "metric visual", "composition": "Clean abstract data visual without readable labels", "export": "1080x1350"}
    if destination == "brand_asset":
        return {"label": "brand asset", "composition": "Reusable background asset with no logo or text", "export": "flexible"}
    return {"label": "vertical", "composition": "Vertical 9:16 composition", "export": "1080x1920"}
