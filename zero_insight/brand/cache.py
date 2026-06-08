from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path

from zero_insight.brand.brand_profile import BrandProfile


def _default_app_data_dir() -> Path:
    configured = os.getenv("ZEROINSIGHT_APP_DATA_DIR", "").strip()
    if configured:
        return Path(configured).expanduser()
    base = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA") or str(Path.home())
    return Path(base) / "ZeroInsight"


def brand_root() -> Path:
    root = _default_app_data_dir() / "brands"
    try:
        root.mkdir(parents=True, exist_ok=True)
        return root
    except PermissionError:
        from zero_insight.config.settings import PROJECT_ROOT

        root = PROJECT_ROOT / ".zeroinsight_appdata" / "brands"
        root.mkdir(parents=True, exist_ok=True)
        return root


def slugify_brand(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower()).strip("_") or "brand"


def brand_dir(brand_name: str) -> Path:
    path = brand_root() / slugify_brand(brand_name)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_source_document(source: Path, target_brand_dir: Path) -> Path:
    target = target_brand_dir / "source" / source.name
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.resolve() != target.resolve():
        shutil.copy2(source, target)
    return target


def save_brand_profile(profile: BrandProfile, directory: Path | None = None) -> Path:
    directory = directory or brand_dir(profile.brand_name)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "brand_profile.json"
    path.write_text(json.dumps(profile.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_brand_profile(identifier: str | Path) -> BrandProfile:
    path = Path(identifier)
    if not path.exists():
        path = brand_dir(str(identifier)) / "brand_profile.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return BrandProfile.from_dict(data)


def list_brand_profiles() -> list[Path]:
    root = brand_root()
    return sorted(root.glob("*/brand_profile.json"), key=lambda p: p.stat().st_mtime, reverse=True)
