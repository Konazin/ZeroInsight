from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from playwright.async_api import async_playwright

from zero_insight.ai import generate_blog_post, save_blog_markdown, test_groq
from zero_insight.brand.cache import load_brand_profile
from zero_insight.browser import extract_data, find_target_page, test_cdp
from zero_insight.browser.extract import has_real_metrics, is_placeholder_payload
from zero_insight.capture import capture_dashboard_screenshot
from zero_insight.config import Settings
from zero_insight.core import LogFn, run_coro
from zero_insight.pipeline.storage import append_jsonl


async def _sleep(seconds: float) -> None:
    import asyncio

    await asyncio.sleep(seconds)


def _log(on_log: LogFn | None, level: str, msg: str) -> None:
    if on_log:
        on_log(level, msg)


async def run_pipeline(
    settings: Settings,
    on_log: LogFn | None = None,
    brand: str | None = None,
) -> tuple[bool, dict[str, Any] | None]:
    _log(on_log, "STEP", "Conectando ao Brave via CDP...")

    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.connect_over_cdp(settings.cdp_url)
            page = await find_target_page(browser, settings)
            _log(on_log, "SUCCESS", f"Sessão Brave anexada — {page.url}")

            attempt = 0
            while attempt < settings.max_retries:
                try:
                    _log(
                        on_log,
                        "INFO",
                        f"Tentativa {attempt + 1}/{settings.max_retries}",
                    )

                    _log(on_log, "STEP", "Extraindo dados da página...")
                    extracted = await extract_data(page, settings)
                    raw = extracted.get("raw")
                    if not raw:
                        raise RuntimeError("Nenhum dado extraído")
                    if is_placeholder_payload(raw) and not has_real_metrics(raw):
                        raise RuntimeError(
                            "Extração retornou apenas placeholders (N/A / 0)."
                        )

                    source = extracted.get("source", "?")
                    _log(on_log, "SUCCESS", f"Dados extraídos via {source.upper()}.")

                    _log(on_log, "STEP", "Capturando screenshot do dashboard...")
                    screenshot_path = await capture_dashboard_screenshot(page, settings)
                    _log(on_log, "SUCCESS", f"Screenshot: {screenshot_path.name}")

                    _log(on_log, "STEP", "Gerando post de blog com IA (visão)...")
                    brand_profile = None
                    if brand:
                        loaded_profile = load_brand_profile(brand)
                        brand_profile = loaded_profile.to_dict()
                        _log(on_log, "INFO", f"Aplicando BrandProfile: {loaded_profile.brand_name}")
                    blog_post = await generate_blog_post(
                        extracted, screenshot_path, settings, brand_profile=brand_profile
                    )
                    blog_post["_saved_at"] = datetime.now(timezone.utc).strftime(
                        "%Y%m%d_%H%M%S"
                    )

                    _log(on_log, "STEP", "Salvando post em Markdown...")
                    post_path = save_blog_markdown(blog_post, settings)

                    _log(on_log, "STEP", "Salvando registro JSONL...")
                    append_jsonl(
                        settings.output_path,
                        {
                            "source": source,
                            "input": extracted["raw"],
                            "screenshot": str(screenshot_path),
                            "blog_post": blog_post,
                            "post_markdown": str(post_path),
                        },
                    )
                    _log(on_log, "SUCCESS", f"Post salvo em {post_path}")

                    return True, {
                        "input": extracted["raw"],
                        "blog_post": blog_post,
                        "screenshot": str(screenshot_path),
                        "post_markdown": str(post_path),
                        "source": source,
                    }
                except Exception as err:
                    _log(on_log, "WARN", str(err))
                    attempt += 1
                    if attempt < settings.max_retries:
                        delay = 1000 * (2 ** (attempt - 1))
                        _log(on_log, "INFO", f"Nova tentativa em {delay}ms...")
                        await _sleep(delay / 1000)
                        try:
                            await page.reload(
                                wait_until="networkidle",
                                timeout=settings.timeout_ms,
                            )
                        except Exception:
                            pass
                    else:
                        _log(on_log, "ERROR", "Máximo de tentativas atingido.")
    except Exception:
        _log(
            on_log,
            "ERROR",
            "Falha ao conectar via CDP. Execute scripts/start_brave_debug.bat",
        )

    return False, None


def run_pipeline_sync(
    settings: Settings,
    on_log: LogFn | None = None,
    brand: str | None = None,
) -> tuple[bool, dict[str, Any] | None]:
    return run_coro(lambda: run_pipeline(settings, on_log, brand=brand))


def test_cdp_sync(settings: Settings) -> tuple[bool, str]:
    return run_coro(lambda: test_cdp(settings))


def test_groq_sync(settings: Settings) -> tuple[bool, str]:
    return run_coro(lambda: test_groq(settings))
