from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from zero_insight.ai_providers import (
    create_image_provider,
    create_text_provider,
    provider_config_from_settings,
)
from zero_insight.brand import BrandValidator
from zero_insight.brand.cache import load_brand_profile
from zero_insight.config import PROJECT_ROOT, Settings
from zero_insight.content import (
    StoryBrief,
    StoryManifest,
    plan_story_script,
    plan_story_script_with_provider,
)
from zero_insight.core import LogFn, run_coro
from zero_insight.image import MockImageProvider
from zero_insight.image.prompt_builder import build_full_composition_prompt, build_image_prompt, build_prompt_package
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


def _create_output_dir(settings: Settings, created_at: datetime, campaign_name: str) -> Path:
    settings.stories_path.mkdir(parents=True, exist_ok=True)
    candidates = [
        settings.stories_path / f"{created_at:%Y%m%d}_{campaign_name}",
        settings.stories_path / f"{created_at:%Y%m%d_%H%M%S_%f}_{campaign_name}",
    ]
    for candidate in candidates:
        try:
            candidate.mkdir(exist_ok=False)
            return candidate
        except FileExistsError:
            continue
    suffix = 2
    while True:
        candidate = settings.stories_path / f"{created_at:%Y%m%d_%H%M%S_%f}_{campaign_name}_{suffix}"
        try:
            candidate.mkdir(exist_ok=False)
            return candidate
        except FileExistsError:
            suffix += 1


async def _load_dino_data(settings: Settings, on_log: LogFn | None) -> dict[str, Any] | None:
    _log(on_log, "STEP", "Tentando reutilizar metricas do Dino via CDP...")
    try:
        from playwright.async_api import async_playwright  # importado só quando Dino é solicitado
        from zero_insight.browser import extract_data, find_target_page
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
    campaign_id = f"{created_at:%Y%m%d_%H%M%S_%f}_{campaign_name}"
    output_dir = _create_output_dir(settings, created_at, campaign_name)

    image_paths: list[Path] = []
    base_paths: list[Path] = []
    slides = []
    validation: dict[str, Any] = {"ok": False, "errors": [], "warnings": []}
    brand_profile = None
    brand_validation: dict[str, Any] | None = None
    image_provider_warnings: list[str] = []
    text_provider_warnings: list[str] = []
    image_prompt_packages: list[dict[str, Any]] = []
    ai_image_metadata: list[dict[str, Any]] = []
    ai_text_metadata: dict[str, Any] = {}
    requested_text_provider = brief.ai_text_provider or settings.default_text_provider or "mock"
    actual_text_provider = requested_text_provider

    try:
        if brief.brand_profile_path or brief.brand_profile_id:
            brand_profile = load_brand_profile(brief.brand_profile_path or brief.brand_profile_id or "")
            _log(on_log, "INFO", f"Aplicando BrandProfile: {brand_profile.brand_name}")
        if from_dino:
            brief.source = "dino"
            brief.dino_data = await _load_dino_data(settings, on_log)

        prompt_validation_text = "\n".join(
            part
            for part in (brief.custom_image_prompt, brief.image_style_instructions)
            if part and part.strip()
        )
        if prompt_validation_text:
            prompt_validation = BrandValidator().validate_content(
                prompt_validation_text,
                brand_profile,
            )
            if prompt_validation["status"] == "FAIL":
                raise RuntimeError(
                    "Prompt de imagem reprovado no compliance: "
                    + "; ".join(prompt_validation["errors"])
                )

        _log(on_log, "STEP", "Gerando roteiro dos Stories...")
        if requested_text_provider == "mock":
            slides = plan_story_script(brief)
            ai_text_metadata = {
                "ai_text_provider": "mock",
                "task_type": "deterministic_story_script",
            }
        else:
            text_config = provider_config_from_settings(
                settings,
                "text",
                requested_text_provider,
            )
            try:
                text_provider = create_text_provider(text_config)
                slides = plan_story_script_with_provider(brief, text_provider)
                ai_text_metadata = dict(
                    getattr(text_provider, "last_manifest", {}) or {}
                )
                ai_text_metadata.setdefault("ai_text_provider", text_provider.name)
                ai_text_metadata.setdefault("ai_text_model", text_config.model)
            except Exception as exc:
                if brief.ai_text_provider:
                    raise RuntimeError(
                        f"Provider de texto '{requested_text_provider}' falhou: {exc}"
                    ) from exc
                warning = (
                    f"Provider de texto '{requested_text_provider}' falhou; "
                    f"usando roteiro determinístico. Motivo: {exc}"
                )
                text_provider_warnings.append(warning)
                _log(on_log, "WARN", warning)
                slides = plan_story_script(brief)
                actual_text_provider = "mock"
                ai_text_metadata = {
                    "ai_text_provider": "mock",
                    "task_type": "deterministic_story_script",
                    "fallback_from": requested_text_provider,
                }
        script_path = output_dir / "story_script.json"
        _write_json(script_path, [slide.to_dict() for slide in slides])

        requested_image_provider = (
            brief.ai_image_provider
            or settings.default_image_provider
            or settings.image_provider
        )
        image_provider_name = requested_image_provider
        mock_provider = MockImageProvider(
            settings.story_width,
            settings.story_height,
            (brand_profile.color_palette[0]["hex"] if brand_profile and brand_profile.color_palette else settings.story_brand_primary_color),
            (brand_profile.color_palette[1]["hex"] if brand_profile and len(brand_profile.color_palette) > 1 else settings.story_brand_secondary_color),
        )
        ai_image_provider = None
        if image_provider_name != "mock":
            try:
                ai_image_provider = create_image_provider(
                    provider_config_from_settings(
                        settings,
                        "image",
                        image_provider_name,
                    )
                )
            except Exception as exc:
                if brief.ai_image_provider:
                    raise
                warning = (
                    f"Provider de imagem '{image_provider_name}' indisponível; "
                    f"usando local. Motivo: {exc}"
                )
                image_provider_warnings.append(warning)
                _log(on_log, "WARN", warning)
                image_provider_name = "local"
                ai_image_provider = create_image_provider(
                    provider_config_from_settings(settings, "image", "local")
                )
            _log(on_log, "INFO", f"Provider de imagem: {ai_image_provider.name}")
        renderer = StoryRenderer(
            settings.story_width,
            settings.story_height,
            brand_profile.brand_name if brand_profile else settings.story_brand_name,
            (brand_profile.color_palette[0]["hex"] if brand_profile and brand_profile.color_palette else settings.story_brand_primary_color),
            (brand_profile.color_palette[1]["hex"] if brand_profile and len(brand_profile.color_palette) > 1 else settings.story_brand_secondary_color),
            str((brand_profile.assets or {}).get("logo_path", "")) if brand_profile else settings.story_logo_path,
        )

        logo_path: str | None = None
        if brand_profile:
            lp = str((brand_profile.assets or {}).get("logo_path", "")).strip()
            if lp:
                from pathlib import Path as _Path
                logo_path = lp if _Path(lp).is_file() else None

        if brief.custom_image_prompt:
            # ── Modo manual: uma única chamada, N imagens de volta ────────────
            count = len(slides)
            _log(on_log, "INFO", f"Modo manual: gerando {count} imagens em uma unica chamada via {image_provider_name}...")
            try:
                manual_provider = ai_image_provider or create_image_provider()
                batch_fn = getattr(manual_provider, "generate_images_batch", None)
                if batch_fn:
                    base_paths_batch = batch_fn(
                        brief.custom_image_prompt, 1024, 1536, output_dir,
                        count, prefix="story", logo_path=logo_path,
                    )
                else:
                    # Provider sem suporte a batch: faz chamadas individuais com o mesmo prompt
                    base_paths_batch = []
                    for slide in slides:
                        bp = output_dir / f"story_{slide.order:02d}_base.png"
                        manual_provider.generate_image(
                            brief.custom_image_prompt,
                            1024,
                            1536,
                            bp,
                            logo_path=logo_path,
                        )
                        base_paths_batch.append(bp)
                _meta = getattr(manual_provider, "last_metadata", {})
                if isinstance(_meta, dict) and _meta:
                    ai_image_metadata.append(_meta)
                logo_was_embedded = bool(_meta.get("logo_embedded", False))
            except Exception as exc:
                if bool(brief.ai_image_provider):
                    raise RuntimeError(f"Provider '{image_provider_name}' falhou na geracao em lote: {exc}") from exc
                _log(on_log, "WARN", f"Batch falhou; usando mock: {exc}")
                base_paths_batch = []
                for slide in slides:
                    bp = output_dir / f"story_{slide.order:02d}_base.png"
                    mock_provider.generate_base_image(brief, slide, bp)
                    base_paths_batch.append(bp)
                logo_was_embedded = False

            for slide, base_path in zip(slides, base_paths_batch):
                final_path = output_dir / f"story_{slide.order:02d}.png"
                prompt_package = build_prompt_package(brief, slide, brand_profile, destination="story")
                prompt_data = prompt_package.to_dict()
                prompt_data.update(
                    {
                        "prompt_mode": "manual",
                        "prompt_sent": brief.custom_image_prompt,
                    }
                )
                image_prompt_packages.append(prompt_data)
                if image_provider_name in {"mock", "local"}:
                    renderer.render(base_path, slide, brief, final_path)
                else:
                    renderer.render_ai_output(
                        base_path,
                        slide,
                        brief,
                        final_path,
                        logo_embedded=logo_was_embedded,
                    )
                base_paths.append(base_path)
                image_paths.append(final_path)

        else:
            # ── Modo assistido: um prompt por slide ───────────────────────────
            for slide in slides:
                base_path = output_dir / f"story_{slide.order:02d}_base.png"
                final_path = output_dir / f"story_{slide.order:02d}.png"
                prompt_package = build_prompt_package(brief, slide, brand_profile, destination="story")
                prompt_data = prompt_package.to_dict()
                if ai_image_provider:
                    prompt = (
                        build_image_prompt(brief, slide, brand_profile)
                        if image_provider_name == "local"
                        else build_full_composition_prompt(
                            brief,
                            slide,
                            brand_profile,
                            logo_path=logo_path,
                        )
                    )
                    prompt_data.update(
                        {
                            "prompt_mode": (
                                "assisted_customized"
                                if brief.image_style_instructions
                                else "assisted"
                            ),
                            "prompt_sent": prompt,
                        }
                    )
                    image_prompt_packages.append(prompt_data)
                    _log(on_log, "INFO", f"Gerando composição completa via {image_provider_name} (slide {slide.order})...")
                    explicit_provider = bool(brief.ai_image_provider)
                    try:
                        ai_image_provider.generate_image(prompt, 1024, 1536, base_path, logo_path=logo_path)
                        metadata = getattr(ai_image_provider, "last_metadata", None)
                        if isinstance(metadata, dict) and metadata:
                            ai_image_metadata.append({"slide_order": slide.order, **metadata})
                    except Exception as exc:
                        if explicit_provider:
                            raise RuntimeError(
                                f"Provider '{image_provider_name}' falhou no slide {slide.order}: {exc}"
                            ) from exc
                        warning = (
                            f"Provider de imagem '{image_provider_name}' falhou no slide "
                            f"{slide.order}; usando geracao local sem API. Motivo: {exc}"
                        )
                        image_provider_warnings.append(warning)
                        _log(on_log, "WARN", warning)
                        fallback_provider = create_image_provider(
                            provider_config_from_settings(settings, "image", "local")
                        )
                        fallback_provider.generate_image(build_image_prompt(brief, slide), 1024, 1536, base_path)
                        base_paths.append(base_path)
                        renderer.render(base_path, slide, brief, final_path)
                        image_paths.append(final_path)
                        continue
                    _meta = getattr(ai_image_provider, "last_metadata", {})
                    logo_was_embedded = bool(_meta.get("logo_embedded", False))
                    if image_provider_name == "local":
                        renderer.render(base_path, slide, brief, final_path)
                    else:
                        renderer.render_ai_output(
                            base_path,
                            slide,
                            brief,
                            final_path,
                            logo_embedded=logo_was_embedded,
                        )
                else:
                    prompt_data.update(
                        {
                            "prompt_mode": "mock",
                            "prompt_sent": build_image_prompt(brief, slide, brand_profile),
                        }
                    )
                    image_prompt_packages.append(prompt_data)
                    mock_provider.generate_base_image(brief, slide, base_path)
                    renderer.render(base_path, slide, brief, final_path)
                base_paths.append(base_path)
                image_paths.append(final_path)

        validation = validate_story_package(
            slides,
            image_paths,
            settings.story_width,
            settings.story_height,
        )
        validation.setdefault("warnings", []).extend(image_provider_warnings)
        validation.setdefault("warnings", []).extend(text_provider_warnings)
        if image_provider_name not in {"mock", "local"}:
            validation.setdefault("warnings", []).append(
                "Texto renderizado por IA exige revisão visual humana; "
                "a validação automática conferiu o roteiro e o prompt, não OCR da imagem final."
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
                "text": actual_text_provider,
                "text_requested": requested_text_provider,
                "text_fallback": "mock" if text_provider_warnings else None,
                "image": image_provider_name,
                "image_requested": requested_image_provider,
                "image_fallback": "local" if image_provider_warnings else None,
            },
            brand_validation=brand_validation,
        )
        manifest_data = manifest.to_dict()
        manifest_data["type"] = "story"
        manifest_data["ai"] = {
            "text_provider": actual_text_provider,
            "text_provider_requested": requested_text_provider,
            "text_model": ai_text_metadata.get("ai_text_model"),
            "image_provider": image_provider_name,
            "image_provider_requested": requested_image_provider,
            "image_model": settings.openai_image_model if image_provider_name == "openai" else None,
            "image_size": settings.openai_image_size if image_provider_name == "openai" else None,
            "image_quality": settings.openai_image_quality if image_provider_name == "openai" else None,
        }
        manifest_data["image_prompts"] = image_prompt_packages
        manifest_data["ai_image_metadata"] = ai_image_metadata
        manifest_data["ai_text_metadata"] = ai_text_metadata
        _write_json(output_dir / "manifest.json", manifest_data)
        _log(on_log, "SUCCESS", f"Pacote de Stories salvo em {output_dir}")
        return bool(validation.get("ok")), manifest_data
    except Exception as exc:
        manifest = StoryManifest(
            id=campaign_id,
            campaign_name=campaign_name,
            status=STATUS_FAILED,
            created_at=created_at.isoformat(),
            brief=brief.to_dict(),
            slides=[slide.to_dict() for slide in slides],
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
