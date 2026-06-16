from __future__ import annotations

from pydantic import BaseModel, Field


class BrandImportRequest(BaseModel):
    path: str = Field(..., description="Local PDF/DOCX path.")
    brand_name: str | None = None
    use_external_ai: bool = False


class BrandProfileResponse(BaseModel):
    id: str
    path: str
    profile: dict

