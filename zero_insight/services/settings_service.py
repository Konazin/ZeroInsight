from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from zero_insight.config import Settings, reload_settings, save_settings
from zero_insight.config.settings import PROJECT_ROOT
from zero_insight.services.brave_manager import default_app_data_dir


class SettingsService:
    def __init__(self) -> None:
        self.app_data_dir = default_app_data_dir()
        self.config_path = self.app_data_dir / "config.json"

    def ensure_app_dirs(self) -> None:
        try:
            for name in ("logs", "cache", "brave-profile"):
                (self.app_data_dir / name).mkdir(parents=True, exist_ok=True)
        except PermissionError:
            self.app_data_dir = PROJECT_ROOT / ".zeroinsight_appdata"
            self.config_path = self.app_data_dir / "config.json"
            for name in ("logs", "cache", "brave-profile"):
                (self.app_data_dir / name).mkdir(parents=True, exist_ok=True)

    def load(self) -> Settings:
        settings = reload_settings()
        if settings.app_data_dir:
            self.app_data_dir = Path(settings.app_data_dir).expanduser()
            self.config_path = self.app_data_dir / "config.json"
        self.ensure_app_dirs()
        return settings

    def save(self, settings: Settings) -> None:
        save_settings(settings)
        self.app_data_dir.mkdir(parents=True, exist_ok=True)
        public_data: dict[str, Any] = asdict(settings)
        if public_data.get("groq_api_key"):
            public_data["groq_api_key"] = "***"
        providers = public_data.get("providers")
        if isinstance(providers, dict):
            public_data["providers"] = self._mask_provider_secrets(providers)
        self.config_path.write_text(
            json.dumps(public_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def update_from_form(settings: Settings, values: dict[str, Any]) -> Settings:
        for key, value in values.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        return settings

    @staticmethod
    def _mask_provider_secrets(providers: dict[str, Any]) -> dict[str, Any]:
        masked = json.loads(json.dumps(providers))
        for by_type in masked.values():
            if isinstance(by_type, dict):
                for config in by_type.values():
                    if isinstance(config, dict) and config.get("api_key_value"):
                        config["api_key_value"] = "***"
        return masked
