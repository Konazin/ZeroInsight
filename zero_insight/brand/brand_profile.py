from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class BrandColor:
    name: str
    hex: str
    usage: str = ""

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass
class BrandProfile:
    brand_name: str
    source_document_path: str
    created_at: str
    summary: str
    tone_of_voice: list[str] = field(default_factory=list)
    forbidden_terms: list[str] = field(default_factory=list)
    preferred_terms: list[str] = field(default_factory=list)
    visual_style: list[str] = field(default_factory=list)
    color_palette: list[dict[str, str]] = field(default_factory=list)
    typography_notes: list[str] = field(default_factory=list)
    logo_usage_notes: list[str] = field(default_factory=list)
    layout_rules: list[str] = field(default_factory=list)
    image_style_rules: list[str] = field(default_factory=list)
    content_rules: list[str] = field(default_factory=list)
    compliance_rules: list[str] = field(default_factory=list)
    target_audience: list[str] = field(default_factory=list)
    cta_style: list[str] = field(default_factory=list)
    examples: list[dict[str, Any]] = field(default_factory=list)
    raw_extracted_text_excerpt: str = ""
    status: str = "needs_review"
    assets: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BrandProfile:
        return cls(
            brand_name=str(data.get("brand_name") or "Marca sem nome"),
            source_document_path=str(data.get("source_document_path") or ""),
            created_at=str(data.get("created_at") or ""),
            summary=str(data.get("summary") or ""),
            tone_of_voice=list(data.get("tone_of_voice") or []),
            forbidden_terms=list(data.get("forbidden_terms") or []),
            preferred_terms=list(data.get("preferred_terms") or []),
            visual_style=list(data.get("visual_style") or []),
            color_palette=list(data.get("color_palette") or []),
            typography_notes=list(data.get("typography_notes") or []),
            logo_usage_notes=list(data.get("logo_usage_notes") or []),
            layout_rules=list(data.get("layout_rules") or []),
            image_style_rules=list(data.get("image_style_rules") or []),
            content_rules=list(data.get("content_rules") or []),
            compliance_rules=list(data.get("compliance_rules") or []),
            target_audience=list(data.get("target_audience") or []),
            cta_style=list(data.get("cta_style") or []),
            examples=list(data.get("examples") or []),
            raw_extracted_text_excerpt=str(data.get("raw_extracted_text_excerpt") or ""),
            status=str(data.get("status") or "needs_review"),
            assets=dict(data.get("assets") or {}),
        )
