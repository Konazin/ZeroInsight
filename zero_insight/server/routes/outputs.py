from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter

from zero_insight.config import PROJECT_ROOT, Settings
from zero_insight.services import OutputService

router = APIRouter(tags=["outputs"])


def _item(kind: str, path: Path) -> dict:
    return {"type": kind, "name": path.name, "path": str(path), "modified_at": path.stat().st_mtime}


@router.get("/outputs")
def outputs() -> list[dict]:
    service = OutputService(Settings.from_env())
    items = [_item("post", path) for path in service.list_posts()]
    items.extend(_item("story", path) for path in service.list_story_campaigns())
    return sorted(items, key=lambda item: item["modified_at"], reverse=True)


@router.get("/logs")
def logs() -> list[str]:
    settings = Settings.from_env()
    candidates = [settings.output_path, PROJECT_ROOT / "results.jsonl"]
    for path in candidates:
        if path.exists():
            return path.read_text(encoding="utf-8", errors="replace").splitlines()[-300:]
    return []

