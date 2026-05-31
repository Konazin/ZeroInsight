from __future__ import annotations

import re
from typing import Any

from playwright.async_api import Page

from automacao_posts.config import Settings


def _parse_br_number(text: str) -> float:
    cleaned = re.sub(r"[^\d,.]", "", text.strip())
    if not cleaned:
        return 0.0
    if "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")
    else:
        parts = cleaned.split(".")
        if len(parts) > 2:
            cleaned = "".join(parts[:-1]) + "." + parts[-1]
        elif len(parts) == 2 and len(parts[1]) == 3:
            cleaned = cleaned.replace(".", "")
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def is_placeholder_payload(raw: dict[str, Any]) -> bool:
    return (
        raw.get("cliente") == "N/A"
        and float(raw.get("valor", 0) or 0) == 0.0
        and raw.get("status") == "desconhecido"
    )


def has_real_metrics(raw: dict[str, Any]) -> bool:
    return bool(raw.get("visualizacoes") or raw.get("distribuicoes_realizadas"))


async def extract_dino_dashboard(page: Page) -> dict[str, Any]:
    scraped = await page.evaluate(
        """() => {
            const box = document.querySelector(
                '.box-resumo-conteudo-trafego.box-resumo-trafego'
            ) || document.querySelector('.box-resumo-trafego');
            if (!box) return null;

            const metricas = {};
            for (const h3 of box.querySelectorAll('h3')) {
                const label = (h3.innerText || '').trim();
                let el = h3.nextElementSibling;
                while (el && !/\\d/.test(el.innerText || '')) {
                    el = el.nextElementSibling;
                }
                metricas[label] = el ? (el.innerText || '').trim() : '';
            }

            return {
                titulo: (document.querySelector('h1')?.innerText || '').trim(),
                metricas,
                url: location.href,
            };
        }"""
    )

    if not scraped or not scraped.get("metricas"):
        raise RuntimeError(
            "Dashboard Dino aberto, mas métricas não encontradas no DOM."
        )

    metricas = scraped["metricas"]
    visualizacoes = _parse_br_number(
        metricas.get("VISUALIZAÇÕES", metricas.get("VISUALIZACOES", "0"))
    )
    distribuicoes = _parse_br_number(
        metricas.get("DISTRIBUIÇÕES REALIZADAS", metricas.get("DISTRIBUICOES REALIZADAS", "0"))
    )

    if visualizacoes == 0.0 and distribuicoes == 0.0:
        raise RuntimeError(f"Métricas zeradas ou ilegíveis: {metricas}")

    return {
        "source": "dino_dashboard",
        "raw": {
            "titulo": scraped.get("titulo", ""),
            "url": scraped.get("url", ""),
            "visualizacoes": int(visualizacoes) if visualizacoes.is_integer() else visualizacoes,
            "distribuicoes_realizadas": int(distribuicoes)
            if distribuicoes.is_integer()
            else distribuicoes,
            "metricas_brutas": metricas,
        },
    }


async def extract_data(page: Page, settings: Settings) -> dict[str, Any]:
    url = page.url.lower()
    if "dino.com.br" in url and "dashboard" in url:
        return await extract_dino_dashboard(page)

    response = None
    try:
        async with page.expect_response(
            lambda res: "/api/dados" in res.url and res.status == 200,
            timeout=settings.timeout_ms,
        ) as response_info:
            if settings.target_url.lower() not in url:
                await page.goto(
                    settings.target_url,
                    wait_until="networkidle",
                    timeout=settings.timeout_ms,
                )
            else:
                await page.reload(
                    wait_until="networkidle",
                    timeout=settings.timeout_ms,
                )
        response = await response_info.value
    except Exception:
        response = None

    if response:
        try:
            raw = await response.json()
            return {"source": "api", "raw": raw}
        except Exception:
            pass

    raise RuntimeError(
        "Página não é o dashboard Dino e nenhuma API /api/dados foi capturada. "
        f"URL atual: {page.url}"
    )
