from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DesktopState:
    busy: bool = False
    last_blog_result: dict[str, Any] | None = None
    last_story_manifest: dict[str, Any] | None = None
    logs: list[tuple[str, str]] = field(default_factory=list)
