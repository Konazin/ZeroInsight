from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from zero_insight.config import Settings


class OutputService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def list_posts(self) -> list[Path]:
        return self._list_files(self.settings.posts_path, "*.md")

    def list_story_campaigns(self) -> list[Path]:
        if not self.settings.stories_path.exists():
            return []
        return sorted(
            [p for p in self.settings.stories_path.iterdir() if p.is_dir()],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

    def open_path(self, path: Path) -> None:
        target = path.resolve()
        if sys.platform == "win32":
            os.startfile(str(target))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(target)])
        else:
            subprocess.Popen(["xdg-open", str(target)])

    def open_parent(self, path: Path) -> None:
        self.open_path(path if path.is_dir() else path.parent)

    @staticmethod
    def _list_files(path: Path, pattern: str) -> list[Path]:
        if not path.exists():
            return []
        return sorted(path.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
