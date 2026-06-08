from __future__ import annotations

import os
import json
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"

ENV_KEYS = (
    "CDP_PORT",
    "BRAVE_EXECUTABLE_PATH",
    "ZEROINSIGHT_APP_DATA_DIR",
    "ZEROINSIGHT_OUTPUT_DIR",
    "ZEROINSIGHT_UI_THEME",
    "TARGET_URL",
    "GROQ_API_KEY",
    "GROQ_ENDPOINT",
    "GROQ_MODEL",
    "GROQ_VISION_MODEL",
    "OUTPUT_FILE",
    "SCREENSHOTS_DIR",
    "POSTS_DIR",
    "BLOG_BRAND_NAME",
    "STORIES_DIR",
    "STORY_WIDTH",
    "STORY_HEIGHT",
    "STORY_DEFAULT_TEMPLATE",
    "STORY_BRAND_NAME",
    "STORY_BRAND_PRIMARY_COLOR",
    "STORY_BRAND_SECONDARY_COLOR",
    "STORY_LOGO_PATH",
    "IMAGE_PROVIDER",
    "DEFAULT_BRAND_PROFILE_ID",
    "DEFAULT_TEXT_PROVIDER",
    "DEFAULT_IMAGE_PROVIDER",
    "DEFAULT_VISION_PROVIDER",
    "ALLOW_EXTERNAL_AI_FOR_BRAND_DOCS",
    "AI_PROVIDERS_JSON",
)

GROQ_MODELS = (
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "mixtral-8x7b-32768",
    "gemma2-9b-it",
)

GROQ_VISION_MODELS = (
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "meta-llama/llama-4-maverick-17b-128e-instruct",
)


@dataclass
class Settings:
    cdp_port: str = "9222"
    brave_executable_path: str = ""
    app_data_dir: str = ""
    output_dir: str = ""
    ui_theme: str = "dark"
    target_url: str = "https://app.dino.com.br/Gerenciador2/dashboard"
    groq_api_key: str = ""
    groq_endpoint: str = "https://api.groq.com/openai/v1/chat/completions"
    groq_model: str = "llama-3.3-70b-versatile"
    groq_vision_model: str = "meta-llama/llama-4-scout-17b-16e-instruct"
    output_file: str = "results.jsonl"
    screenshots_dir: str = "screenshots"
    posts_dir: str = "posts"
    blog_brand_name: str = "Sua Legal Tech"
    stories_dir: str = "stories"
    story_width: int = 1080
    story_height: int = 1920
    story_default_template: str = "legal_clean"
    story_brand_name: str = "Requisite"
    story_brand_primary_color: str = "#111827"
    story_brand_secondary_color: str = "#2563EB"
    story_logo_path: str = ""
    image_provider: str = "mock"
    default_brand_profile_id: str = ""
    default_text_provider: str = "mock"
    default_image_provider: str = "mock"
    default_vision_provider: str = "mock"
    allow_external_ai_for_brand_docs: bool = False
    providers: dict[str, object] | None = None
    max_retries: int = 3
    timeout_ms: int = 15_000

    @property
    def output_path(self) -> Path:
        return self._base_output_path() / self.output_file

    @property
    def screenshots_path(self) -> Path:
        return self._base_output_path() / self.screenshots_dir

    @property
    def posts_path(self) -> Path:
        return self._base_output_path() / self.posts_dir

    @property
    def stories_path(self) -> Path:
        return self._base_output_path() / self.stories_dir

    def _base_output_path(self) -> Path:
        return Path(self.output_dir).expanduser() if self.output_dir else PROJECT_ROOT

    @property
    def cdp_url(self) -> str:
        return f"http://127.0.0.1:{self.cdp_port}"

    def masked_api_key(self) -> str:
        if not self.groq_api_key:
            return "(não configurada)"
        if len(self.groq_api_key) <= 8:
            return "****"
        return f"{self.groq_api_key[:4]}...{self.groq_api_key[-4:]}"

    def to_env_dict(self) -> dict[str, str]:
        return {
            "CDP_PORT": self.cdp_port,
            "BRAVE_EXECUTABLE_PATH": self.brave_executable_path,
            "ZEROINSIGHT_APP_DATA_DIR": self.app_data_dir,
            "ZEROINSIGHT_OUTPUT_DIR": self.output_dir,
            "ZEROINSIGHT_UI_THEME": self.ui_theme,
            "TARGET_URL": self.target_url,
            "GROQ_API_KEY": self.groq_api_key,
            "GROQ_ENDPOINT": self.groq_endpoint,
            "GROQ_MODEL": self.groq_model,
            "GROQ_VISION_MODEL": self.groq_vision_model,
            "OUTPUT_FILE": self.output_file,
            "SCREENSHOTS_DIR": self.screenshots_dir,
            "POSTS_DIR": self.posts_dir,
            "BLOG_BRAND_NAME": self.blog_brand_name,
            "STORIES_DIR": self.stories_dir,
            "STORY_WIDTH": str(self.story_width),
            "STORY_HEIGHT": str(self.story_height),
            "STORY_DEFAULT_TEMPLATE": self.story_default_template,
            "STORY_BRAND_NAME": self.story_brand_name,
            "STORY_BRAND_PRIMARY_COLOR": self.story_brand_primary_color,
            "STORY_BRAND_SECONDARY_COLOR": self.story_brand_secondary_color,
            "STORY_LOGO_PATH": self.story_logo_path,
            "IMAGE_PROVIDER": self.image_provider,
            "DEFAULT_BRAND_PROFILE_ID": self.default_brand_profile_id,
            "DEFAULT_TEXT_PROVIDER": self.default_text_provider,
            "DEFAULT_IMAGE_PROVIDER": self.default_image_provider,
            "DEFAULT_VISION_PROVIDER": self.default_vision_provider,
            "ALLOW_EXTERNAL_AI_FOR_BRAND_DOCS": "true" if self.allow_external_ai_for_brand_docs else "false",
            "AI_PROVIDERS_JSON": json.dumps(self.providers or {}, ensure_ascii=False),
        }

    @classmethod
    def from_env(cls) -> Settings:
        load_dotenv(ENV_PATH, override=True)
        return cls(
            cdp_port=os.getenv("CDP_PORT", "9222"),
            brave_executable_path=os.getenv("BRAVE_EXECUTABLE_PATH", ""),
            app_data_dir=os.getenv("ZEROINSIGHT_APP_DATA_DIR", ""),
            output_dir=os.getenv("ZEROINSIGHT_OUTPUT_DIR", ""),
            ui_theme=os.getenv("ZEROINSIGHT_UI_THEME", "dark"),
            target_url=os.getenv(
                "TARGET_URL", "https://app.dino.com.br/Gerenciador2/dashboard"
            ),
            groq_api_key=os.getenv("GROQ_API_KEY", ""),
            groq_endpoint=os.getenv(
                "GROQ_ENDPOINT", "https://api.groq.com/openai/v1/chat/completions"
            ),
            groq_model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            groq_vision_model=os.getenv(
                "GROQ_VISION_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct"
            ),
            output_file=os.getenv("OUTPUT_FILE", "results.jsonl"),
            screenshots_dir=os.getenv("SCREENSHOTS_DIR", "screenshots"),
            posts_dir=os.getenv("POSTS_DIR", "posts"),
            blog_brand_name=os.getenv("BLOG_BRAND_NAME", "Sua Legal Tech"),
            stories_dir=os.getenv("STORIES_DIR", "stories"),
            story_width=int(os.getenv("STORY_WIDTH", "1080")),
            story_height=int(os.getenv("STORY_HEIGHT", "1920")),
            story_default_template=os.getenv("STORY_DEFAULT_TEMPLATE", "legal_clean"),
            story_brand_name=os.getenv("STORY_BRAND_NAME", "Requisite"),
            story_brand_primary_color=os.getenv("STORY_BRAND_PRIMARY_COLOR", "#111827"),
            story_brand_secondary_color=os.getenv("STORY_BRAND_SECONDARY_COLOR", "#2563EB"),
            story_logo_path=os.getenv("STORY_LOGO_PATH", ""),
            image_provider=os.getenv("IMAGE_PROVIDER", "mock"),
            default_brand_profile_id=os.getenv("DEFAULT_BRAND_PROFILE_ID", ""),
            default_text_provider=os.getenv("DEFAULT_TEXT_PROVIDER", "mock"),
            default_image_provider=os.getenv("DEFAULT_IMAGE_PROVIDER", "mock"),
            default_vision_provider=os.getenv("DEFAULT_VISION_PROVIDER", "mock"),
            allow_external_ai_for_brand_docs=os.getenv("ALLOW_EXTERNAL_AI_FOR_BRAND_DOCS", "false").lower()
            in {"1", "true", "yes", "sim"},
            providers=_parse_json_env("AI_PROVIDERS_JSON"),
        )


def _parse_json_env(key: str) -> dict[str, object]:
    raw = os.getenv(key, "").strip()
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def reload_settings() -> Settings:
    return Settings.from_env()


def save_settings(settings: Settings) -> None:
    values = settings.to_env_dict()
    lines: list[str] = []
    seen: set[str] = set()

    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and "=" in line:
                key = line.split("=", 1)[0].strip()
                if key in values:
                    lines.append(f"{key}={values[key]}")
                    seen.add(key)
                    continue
            lines.append(line)

    for key in ENV_KEYS:
        if key not in seen:
            lines.append(f"{key}={values[key]}")

    ENV_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    load_dotenv(ENV_PATH, override=True)
