from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class StoryBrief:
    topic: str
    objective: str
    audience: str
    tone: str
    cta: str
    slides: int
    template: str
    source: str = "manual"
    dino_data: dict[str, Any] | None = None
    brand_profile_id: str | None = None
    brand_profile_path: str | None = None
    ai_text_provider: str | None = None
    ai_image_provider: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class StorySlide:
    order: int
    hook: str
    body: str
    cta: str
    visual_idea: str
    image_prompt: str
    compliance_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class StoryManifest:
    id: str
    campaign_name: str
    status: str
    created_at: str
    brief: dict[str, Any]
    slides: list[dict[str, Any]]
    outputs: dict[str, Any]
    validation: dict[str, Any]
    brand_profile_used: dict[str, Any] | None = None
    ai_providers_used: dict[str, Any] | None = None
    brand_validation: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
