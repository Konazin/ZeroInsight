from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"

ENV_KEYS = (
    "CDP_PORT",
    "TARGET_URL",
    "GROQ_API_KEY",
    "GROQ_ENDPOINT",
    "GROQ_MODEL",
    "GROQ_VISION_MODEL",
    "OUTPUT_FILE",
    "SCREENSHOTS_DIR",
    "POSTS_DIR",
    "BLOG_BRAND_NAME",
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
    target_url: str = "https://app.dino.com.br/Gerenciador2/dashboard"
    groq_api_key: str = ""
    groq_endpoint: str = "https://api.groq.com/openai/v1/chat/completions"
    groq_model: str = "llama-3.3-70b-versatile"
    groq_vision_model: str = "meta-llama/llama-4-scout-17b-16e-instruct"
    output_file: str = "results.jsonl"
    screenshots_dir: str = "screenshots"
    posts_dir: str = "posts"
    blog_brand_name: str = "Sua Legal Tech"
    max_retries: int = 3
    timeout_ms: int = 15_000

    @property
    def output_path(self) -> Path:
        return PROJECT_ROOT / self.output_file

    @property
    def screenshots_path(self) -> Path:
        return PROJECT_ROOT / self.screenshots_dir

    @property
    def posts_path(self) -> Path:
        return PROJECT_ROOT / self.posts_dir

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
            "TARGET_URL": self.target_url,
            "GROQ_API_KEY": self.groq_api_key,
            "GROQ_ENDPOINT": self.groq_endpoint,
            "GROQ_MODEL": self.groq_model,
            "GROQ_VISION_MODEL": self.groq_vision_model,
            "OUTPUT_FILE": self.output_file,
            "SCREENSHOTS_DIR": self.screenshots_dir,
            "POSTS_DIR": self.posts_dir,
            "BLOG_BRAND_NAME": self.blog_brand_name,
        }

    @classmethod
    def from_env(cls) -> Settings:
        load_dotenv(ENV_PATH, override=True)
        return cls(
            cdp_port=os.getenv("CDP_PORT", "9222"),
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
        )


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
