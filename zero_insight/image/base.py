from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from zero_insight.content import StoryBrief, StorySlide


class ImageProvider(ABC):
    @abstractmethod
    def generate_base_image(
        self,
        brief: StoryBrief,
        slide: StorySlide,
        output_path: Path,
    ) -> Path:
        raise NotImplementedError
