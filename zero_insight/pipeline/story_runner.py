from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from playwright.async_api import async_playwright

from zero_insight.browser import extract_data, find_target_page
from zero_insight.brand import BrandValidator
from zero_insight.brand.cache import load_brand_profile
from zero_insight.config import PROJECT_ROOT, Settings
from zero_insight.content import StoryBrief, StoryManifest, plan_story_script
from zero_insight.core import LogFn, run_coro
from zero_insight.image import MockImageProvider
from zero_insight.qa import validate_story_package
from zero_insight.render import StoryRenderer, write_review_page

STATUS_CREATED = "CREATED"
STATUS_SCRIPT_GENERATED = "SCRIPT_GENERATED"
STATUS_IMAGE_GENERATED = "IMAGE_GENERATED"
STATUS_RENDERED = "RENDERED"
STATUS_VALIDATED = "VALIDATED"
STATUS_AWAITING_REVIEW = "AWAITING_REVIEW"
STATUS_FAILED = "FAILED"


def _log(on_log: LogFn | None, level: str, msg: str) -> None:
    if on_log:
        on_log(level, msg)


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower()).strip("_")
    return normalized or "story"


def _relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def _write_json(path: Path, data: dict[str, Any] | list[dict[str, Any]]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


async def _load_dino_data(settings: Settings, on_log: LogFn | None) -> dict[str, Any] | None:
    _log(on_log, "STEP", "Tentando reutilizar metricas do Dino via CDP...")
    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.connect_over_cdp(settings.cdp_url)
            page = await find_target_page(browser, settings)
            extracted = await extract_data(page, settings)
            raw = extracted.get("raw")
            if isinstance(raw, dict):
                _log(on_log, "SUCCESS", "Metricas Dino carregadas para o roteiro.")
                return raw
    except Exception as exc:
        _log(on_log, "WARN", f"Nao foi possivel carregar Dino; seguindo manual: {exc}")
    return None


async def run_story_pipeline(
    settings: Settings,
    brief: StoryBrief,
    from_dino: bool = False,
    on_log: LogFn | None = None,
) -> tuple[bool, dict[str, Any] | None]:
    created_at = datetime.now(timezone.utc)
    campaign_name = _slugify(brief.topic)
    campaign_id = f"{created_at:%Y%m%d_%H%M%S}_{campaign_name}"
    output_dir = settings.stories_path / f"{created_at:%Y%m%d}_{campaign_name}"
    if output_dir.exists():
        output_dir = settings.stories_path / campaign_id
    output_dir.mkdir(parents=True, exist_ok=True)

    image_paths: list[Path] = []
    base_paths: list[Path] = []
    validation: dict[str, Any] = {"ok": False, "errors": [], "warnings": []}
    brand_profile = None
    brand_validation: dict[str, Any] | None = None

    try:
        if brief.brand_profile_path or brief.brand_profile_id:
            brand_profile = load_brand_profile(brief.brand_profile_path or brief.brand_profile_id or "")
            _log(on_log, "INFO", f"Aplicando BrandProfile: {brand_profile.brand_name}")
        if from_dino:
            brief.source = "dino"
            brief.dino_data = await _load_dino_data(settings, on_log)

        _log(on_log, "STEP", "Gerando roteiro dos Stories...")
        slides = plan_story_script(brief)
        script_path = output_dir / "story_script.json"
        _write_json(script_path, [slide.to_dict() for slide in slides])

        if settings.image_provider != "mock":
            _log(on_log, "WARN", "Provider nao implementado; usando mock.")

        provider = MockImageProvider(
            settings.story_width,
            settings.story_height,
            (brand_profile.color_palette[0]["hex"] if brand_profile and brand_profile.color_palette else settings.story_brand_primary_color),
            (brand_profile.color_palette[1]["hex"] if brand_profile and len(brand_profile.color_palette) > 1 else settings.story_brand_secondary_color),
        )
        renderer = StoryRenderer(
            settings.story_width,
            settings.story_height,
            brand_profile.brand_name if brand_profile else settings.story_brand_name,
            (brand_profile.color_palette[0]["hex"] if brand_profile and brand_profile.color_palette else settings.story_brand_primary_color),
            (brand_profile.color_palette[1]["hex"] if brand_profile and len(brand_profile.color_palette) > 1 else settings.story_brand_secondary_color),
            str((brand_profile.assets or {}).get("logo_path", "")) if brand_profile else settings.story_logo_path,
        )

        for slide in slides:
            base_path = output_dir / f"story_{slide.order:02d}_base.png"
            final_path = output_dir / f"story_{slide.order:02d}.png"
            provider.generate_base_image(brief, slide, base_path)
            base_paths.append(base_path)
            renderer.render(base_path, slide, brief, final_path)
            image_paths.append(final_path)

        validation = validate_story_package(
            slides,
            image_paths,
            settings.story_width,
            settings.story_height,
        )
        joined_text = "\n".join(f"{slide.hook}\n{slide.body}\n{slide.cta}" for slide in slides)
        brand_validation = BrandValidator().validate_content(joined_text, brand_profile)
        if brand_validation["status"] == "FAIL":
            validation["ok"] = False
            validation.setdefault("errors", []).extend(brand_validation["errors"])
        status = STATUS_VALIDATED if validation.get("ok") else STATUS_FAILED

        review_path = output_dir / "review.html"
        write_review_page(review_path, brief, slides, image_paths, validation)
        if validation.get("ok"):
            status = STATUS_AWAITING_REVIEW

        manifest = StoryManifest(
            id=campaign_id,
            campaign_name=campaign_name,
            status=status,
            created_at=created_at.isoformat(),
            brief=brief.to_dict(),
            slides=[slide.to_dict() for slide in slides],
            outputs={
                "directory": _relative(output_dir),
                "manifest": _relative(output_dir / "manifest.json"),
                "story_script": _relative(script_path),
                "review": _relative(review_path),
                "images": [_relative(path) for path in image_paths],
                "base_images": [_relative(path) for path in base_paths],
            },
            validation=validation,
            brand_profile_used=brand_profile.to_dict() if brand_profile else None,
            ai_providers_used={
                "text": brief.ai_text_provider or settings.default_text_provider,
                "image": brief.ai_image_provider or settings.default_image_provider,
            },
            brand_validation=brand_validation,
        )
        _write_json(output_dir / "manifest.json", manifest.to_dict())
        _log(on_log, "SUCCESS", f"Pacote de Stories salvo em {output_dir}")
        return bool(validation.get("ok")), manifest.to_dict()
    except Exception as exc:
        manifest = StoryManifest(
            id=campaign_id,
            campaign_name=campaign_name,
            status=STATUS_FAILED,
            created_at=created_at.isoformat(),
            brief=brief.to_dict(),
            slides=[],
            outputs={"directory": _relative(output_dir)},
            validation={"ok": False, "errors": [str(exc)], "warnings": []},
        )
        _write_json(output_dir / "manifest.json", manifest.to_dict())
        _log(on_log, "ERROR", f"Pipeline de Stories falhou: {exc}")
        return False, manifest.to_dict()


def run_story_pipeline_sync(
    settings: Settings,
    brief: StoryBrief,
    from_dino: bool = False,
    on_log: LogFn | None = None,
) -> tuple[bool, dict[str, Any] | None]:
    return run_coro(lambda: run_story_pipeline(settings, brief, from_dino, on_log))
