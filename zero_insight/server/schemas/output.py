from __future__ import annotations

from pydantic import BaseModel


class OutputItem(BaseModel):
    type: str
    name: str
    path: str
    modified_at: float

