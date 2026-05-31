from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from playwright.async_api import Page

from automacao_posts.config import Settings


async def capture_dashboard_screenshot(page: Page, settings: Settings) -> Path:
    settings.screenshots_path.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    viewport_path = settings.screenshots_path / f"dashboard_{ts}.png"
    await page.screenshot(path=str(viewport_path), full_page=False, type="png")

    resumo = page.locator(".box-resumo-conteudo-trafego.box-resumo-trafego").first
    try:
        if await resumo.count() > 0:
            crop_path = settings.screenshots_path / f"resumo_{ts}.png"
            await resumo.screenshot(path=str(crop_path), type="png")
    except Exception:
        pass

    return viewport_path.resolve()
