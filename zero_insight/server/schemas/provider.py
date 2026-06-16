from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class ProviderTestRequest(BaseModel):
    kind: Literal["text", "image", "vision"]
    name: str
    prompt: str = "Responda ok"

