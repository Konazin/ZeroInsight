from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from zero_insight.ai_providers import ProviderConfig, create_image_provider
from zero_insight.brand import BrandValidator
from zero_insight.brand.cache import load_brand_profile
from zero_insight.config import PROJECT_ROOT, Settings
from zero_insight.content import StoryBrief, StoryManifest, plan_story_script
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


def _provider_config(settings: Settings, kind: str, name: str) -> ProviderConfig:
    providers = settings.providers or {}
    raw = providers.get(kind, {}).get(name, {}) if isinstance(providers, dict) else {}
    config = ProviderConfig(
        provider_type=kind,  # type: ignore[arg-type]
        provider_name=name,
        model=str(raw.get("model") or ""),
        api_key_env=raw.get("api_key_env"),
        api_key_value=raw.get("api_key_value"),
        base_url=raw.get("base_url"),
        endpoint=raw.get("endpoint"),
        extra_headers=dict(raw.get("extra_headers") or {}),
        extra_params=dict(raw.get("extra_params") or {}),
    )
    if name == "openai":
        config.api_key_value = config.api_key_value or settings.openai_api_key or None
        config.base_url = config.base_url or settings.openai_base_url or None
        if kind == "image":
            config.model = config.model or settings.openai_image_model
            config.extra_params.setdefault("size", settings.openai_image_size)
            config.extra_params.setdefault("quality", settings.openai_image_quality)
            config.extra_params.setdefault("format", settings.openai_image_format)
            config.extra_params.setdefault("background", settings.openai_image_background)
        elif kind == "text":
            config.model = config.model or settings.openai_text_model
        elif kind == "vision":
            config.model = config.model or settings.openai_vision_model
    if name == "custom":
        if kind == "text":
            config.api_key_value = config.api_key_value or settings.custom_text_api_key or None
            config.base_url = config.base_url or settings.custom_text_base_url or None
            config.endpoint = config.endpoint or settings.custom_text_endpoint or None
            config.model = config.model or settings.custom_text_model
        if kind == "image":
            config.api_key_value = config.api_key_value or settings.custom_image_api_key or None
            config.base_url = config.base_url or settings.custom_image_base_url or None
            config.endpoint = config.endpoint or settings.custom_image_endpoint or None
            config.model = config.model or settings.custom_image_model
    if name == "local" and kind == "image":
        config.model = config.model or settings.local_image_model_path
    return config


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
    image_provider_warnings: list[str] = []
    image_prompt_packages: list[dict[str, Any]] = []
    ai_image_metadata: list[dict[str, Any]] = []

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

        image_provider_name = brief.ai_image_provider or settings.default_image_provider or settings.image_provider
        mock_provider = MockImageProvider(
            settings.story_width,
            settings.story_height,
            (brand_profile.color_palette[0]["hex"] if brand_profile and brand_profile.color_palette else settings.story_brand_primary_color),
            (brand_profile.color_palette[1]["hex"] if brand_profile and len(brand_profile.color_palette) > 1 else settings.story_brand_secondary_color),
        )
        ai_image_provider = None
        if image_provider_name != "mock":
            ai_image_provider = create_image_provider(_provider_config(settings, "image", image_provider_name))
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

        for slide in slides:
            base_path = output_dir / f"story_{slide.order:02d}_base.png"
            final_path = output_dir / f"story_{slide.order:02d}.png"
            prompt_package = build_prompt_package(brief, slide, brand_profile, destination="story")
            image_prompt_packages.append(prompt_package.to_dict())
            if ai_image_provider:
                # Composição completa: IA gera o story inteiro com texto embutido
                if brief.custom_image_prompt:
                    prompt = brief.custom_image_prompt
                else:
                    prompt = build_full_composition_prompt(brief, slide, brand_profile, logo_path=logo_path)
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
                    fallback_provider = create_image_provider(_provider_config(settings, "image", "local"))
                    fallback_provider.generate_image(build_image_prompt(brief, slide), 1024, 1536, base_path)
                    # Fallback usa renderer completo pois gerou só o fundo
                    base_paths.append(base_path)
                    renderer.render(base_path, slide, brief, final_path)
                    image_paths.append(final_path)
                    continue
                # Sucesso com IA: não aplica overlay de texto — a imagem já é a composição final
                _meta = getattr(ai_image_provider, "last_metadata", {})
                logo_was_embedded = bool(_meta.get("logo_embedded", False))
                renderer.render_ai_output(base_path, slide, brief, final_path, logo_embedded=logo_was_embedded)
            else:
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
                "image": image_provider_name,
                "image_fallback": "local" if image_provider_warnings else None,
            },
            brand_validation=brand_validation,
        )
        manifest_data = manifest.to_dict()
        manifest_data["type"] = "story"
        manifest_data["ai"] = {
            "text_provider": brief.ai_text_provider or settings.default_text_provider,
            "text_model": settings.openai_text_model
            if (brief.ai_text_provider or settings.default_text_provider) == "openai"
            else None,
            "image_provider": image_provider_name,
            "image_model": settings.openai_image_model if image_provider_name == "openai" else None,
            "image_size": settings.openai_image_size if image_provider_name == "openai" else None,
            "image_quality": settings.openai_image_quality if image_provider_name == "openai" else None,
        }
        manifest_data["image_prompts"] = image_prompt_packages
        manifest_data["ai_image_metadata"] = ai_image_metadata
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
