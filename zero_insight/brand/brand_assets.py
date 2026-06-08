from __future__ import annotations

from pathlib import Path


def find_first_logo(assets_dir: Path) -> Path | None:
    if not assets_dir.exists():
        return None
    for path in sorted(assets_dir.iterdir()):
        name = path.name.lower()
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"} and "logo" in name:
            return path
    for path in sorted(assets_dir.iterdir()):
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
            return path
    return None
