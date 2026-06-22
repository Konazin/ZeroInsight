from __future__ import annotations

from typing import TYPE_CHECKING

import httpx

from zero_insight.config import Settings

if TYPE_CHECKING:
    from playwright.async_api import Browser, Page


async def find_target_page(browser: Browser, settings: Settings) -> Page:
    target = settings.target_url.lower()
    host = "dino.com.br"
    candidates: list[Page] = []

    for context in browser.contexts:
        for page in context.pages:
            url = page.url.lower()
            if host in url and "dashboard" in url:
                candidates.append(page)

    if not candidates:
        raise RuntimeError(
            "Nenhuma aba do Dino dashboard encontrada. "
            f"Abra {settings.target_url} no Brave com debug ativo."
        )

    for page in candidates:
        if page.url.lower().rstrip("/") == target.rstrip("/"):
            return page

    return candidates[0]


async def test_cdp(settings: Settings) -> tuple[bool, str]:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.get(f"{settings.cdp_url}/json/version")
        if res.is_success:
            browser = res.json().get("Browser", "desconhecido")
            return True, f"Brave conectado ({browser})"
        return False, f"CDP respondeu com status {res.status_code}"
    except Exception as err:
        return False, (
            "Não foi possível conectar. Execute scripts/start_brave_debug.bat "
            f"ou use --remote-debugging-port={settings.cdp_port}"
        ) + f" — {err}"
