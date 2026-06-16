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


def fallback_brand_root() -> Path:
    from zero_insight.config.settings import PROJECT_ROOT

    return PROJECT_ROOT / ".zeroinsight_appdata" / "brands"


def slugify_brand(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower()).strip("_") or "brand"


def brand_dir(brand_name: str) -> Path:
    slug = slugify_brand(brand_name)
    path = brand_root() / slug
    try:
        path.mkdir(parents=True, exist_ok=True)
        return path
    except PermissionError:
        fallback = fallback_brand_root() / slug
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def save_source_document(source: Path, target_brand_dir: Path) -> Path:
    target = target_brand_dir / "source" / source.name
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.resolve() != target.resolve():
            shutil.copy2(source, target)
        return target
    except PermissionError:
        fallback = fallback_brand_root() / target_brand_dir.name / "source" / source.name
        fallback.parent.mkdir(parents=True, exist_ok=True)
        if source.resolve() != fallback.resolve():
            shutil.copy2(source, fallback)
        return fallback


def save_brand_profile(profile: BrandProfile, directory: Path | None = None) -> Path:
    directory = directory or brand_dir(profile.brand_name)
    try:
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / "brand_profile.json"
        path.write_text(json.dumps(profile.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return path
    except PermissionError:
        fallback = fallback_brand_root() / directory.name
        fallback.mkdir(parents=True, exist_ok=True)
        path = fallback / "brand_profile.json"
        path.write_text(json.dumps(profile.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return path


def load_brand_profile(identifier: str | Path) -> BrandProfile:
    path = Path(identifier)
    if not path.exists():
        slug = slugify_brand(str(identifier))
        candidates = [
            brand_root() / slug / "brand_profile.json",
            fallback_brand_root() / slug / "brand_profile.json",
        ]
        path = next((candidate for candidate in candidates if candidate.exists()), candidates[0])
    data = json.loads(path.read_text(encoding="utf-8"))
    return BrandProfile.from_dict(data)


def list_brand_profiles() -> list[Path]:
    roots = [brand_root(), fallback_brand_root()]
    paths: dict[str, Path] = {}
    for root in roots:
        if root.exists():
            for path in root.glob("*/brand_profile.json"):
                paths[str(path.resolve()).lower()] = path
    return sorted(paths.values(), key=lambda p: p.stat().st_mtime, reverse=True)
