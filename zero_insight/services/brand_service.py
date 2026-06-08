from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from zero_insight.ai_providers import ProviderConfig, create_text_provider
from zero_insight.brand import BrandExtractor, BrandProfile, BrandValidator, DocumentLoader
from zero_insight.brand.cache import brand_dir, list_brand_profiles, save_brand_profile, save_source_document, slugify_brand
from zero_insight.config import Settings


class BrandService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def import_document(
        self,
        document_path: Path,
        brand_name: str | None = None,
        use_external_ai: bool = False,
        on_log=None,
    ) -> tuple[BrandProfile, Path]:
        target_name = brand_name or document_path.stem
        directory = brand_dir(target_name)
        source_path = save_source_document(document_path, directory)
        assets_dir = directory / "assets"
        if on_log:
            on_log("INFO", f"Extraindo texto de {document_path.name}.")
        loaded = DocumentLoader().load(source_path, assets_dir=assets_dir)
        if on_log:
            for warning in loaded.warnings:
                on_log("WARN", warning)

        provider = None
        if use_external_ai and self.settings.allow_external_ai_for_brand_docs:
            provider = create_text_provider(self._provider_config("text", self.settings.default_text_provider))
            if on_log:
                on_log("INFO", f"Usando provider texto: {provider.name}")
        elif on_log:
            on_log("INFO", "Usando extracao local heuristica/mock; documento nao sera enviado a IA externa.")

        profile = BrandExtractor(provider).extract(
            loaded,
            brand_name=brand_name,
            assets_dir=assets_dir,
            allow_external_ai=bool(provider),
        )
        validation = BrandValidator().validate_profile(profile)
        profile.assets["validation"] = validation
        profile_path = save_brand_profile(profile, directory)
        if on_log:
            on_log("SUCCESS", f"BrandProfile salvo em {profile_path}")
        return profile, profile_path

    def list_profiles(self) -> list[Path]:
        return list_brand_profiles()

    def load_profile(self, brand: str) -> BrandProfile:
        from zero_insight.brand.cache import load_brand_profile

        return load_brand_profile(brand)

    def save_profile_from_json(self, raw_json: str) -> Path:
        data = json.loads(raw_json)
        profile = BrandProfile.from_dict(data)
        return save_brand_profile(profile, brand_dir(profile.brand_name))

    def _provider_config(self, kind: str, name: str) -> ProviderConfig:
        providers: dict[str, Any] = self.settings.providers or {}
        raw = providers.get(kind, {}).get(name, {}) if isinstance(providers, dict) else {}
        return ProviderConfig(
            provider_type=kind,  # type: ignore[arg-type]
            provider_name=name or "mock",
            model=str(raw.get("model") or ""),
            api_key_env=raw.get("api_key_env"),
            api_key_value=raw.get("api_key_value"),
            base_url=raw.get("base_url"),
            endpoint=raw.get("endpoint"),
            extra_headers=dict(raw.get("extra_headers") or {}),
            extra_params=dict(raw.get("extra_params") or {}),
        )

    @staticmethod
    def profile_label(path: Path) -> str:
        return slugify_brand(path.parent.name)
