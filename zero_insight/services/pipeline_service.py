from __future__ import annotations

from typing import Any

from zero_insight.config import Settings
from zero_insight.content import StoryBrief
from zero_insight.pipeline import run_pipeline_sync, run_story_pipeline_sync


class PipelineService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def run_blog(self, on_log=None, brand: str | None = None) -> tuple[bool, dict[str, Any] | None]:
        return run_pipeline_sync(self.settings, on_log=on_log, brand=brand)

    def run_stories(
        self,
        brief: StoryBrief,
        from_dino: bool = False,
        on_log=None,
    ) -> tuple[bool, dict[str, Any] | None]:
        return run_story_pipeline_sync(
            self.settings,
            brief,
            from_dino=from_dino,
            on_log=on_log,
        )
