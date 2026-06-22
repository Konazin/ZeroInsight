from __future__ import annotations

from pydantic import BaseModel


class SavePromptRequest(BaseModel):
    name: str
    prompt: str
    description: str = ""
    brand_id: str | None = None
    tags: list[str] = []


class UpdatePromptRequest(BaseModel):
    name: str | None = None
    prompt: str | None = None
    description: str | None = None
    brand_id: str | None = None
    tags: list[str] | None = None
