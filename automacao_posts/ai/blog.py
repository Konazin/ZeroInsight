from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from automacao_posts.config import Settings

BLOG_SCHEMA = """
{
  "titulo": "string (max 90 caracteres, chamativo)",
  "subtitulo": "string",
  "corpo_markdown": "string (800-1200 palavras, markdown)",
  "tags": ["string", "..."],
  "cta": "string (call-to-action para startup juridica)",
  "meta_descricao": "string (max 160 caracteres, SEO)"
}
"""


def _encode_image(path: Path) -> tuple[str, str]:
    suffix = path.suffix.lower().lstrip(".")
    mime = {"png": "png", "jpg": "jpeg", "jpeg": "jpeg", "webp": "webp"}.get(
        suffix, "png"
    )
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return mime, data


def _build_prompt(extracted: dict[str, Any], brand: str) -> str:
    raw = extracted.get("raw", {})
    source = extracted.get("source", "desconhecido")
    return f"""Você é redator sênior do blog de uma startup jurídica brasileira chamada "{brand}".

Com base nos DADOS ESTRUTURADOS abaixo e na IMAGEM do dashboard anexada, escreva um post de blog
profissional, informativo e com tom de autoridade (sem juridiquês excessivo).

Público-alvo: advogados, gestores de escritórios e founders de legal tech.

Regras:
- Use os números reais dos dados (visualizações, distribuições, etc.)
- Referencie insights visuais da imagem quando relevante
- Inclua 1 seção sobre tendências de distribuição de conteúdo jurídico digital
- Não invente métricas que não estejam nos dados
- Tom: moderno, confiável, orientado a resultados
- Idioma: português do Brasil

Fonte dos dados: {source}
Dados JSON:
{json.dumps(raw, ensure_ascii=False, indent=2)}

Responda APENAS com JSON válido neste schema:
{BLOG_SCHEMA}
"""


async def generate_blog_post(
    extracted: dict[str, Any],
    screenshot_path: Path,
    settings: Settings,
) -> dict[str, Any]:
    if not settings.groq_api_key:
        raise RuntimeError("GROQ_API_KEY não configurada")

    if not screenshot_path.is_file():
        raise RuntimeError(f"Screenshot não encontrado: {screenshot_path}")

    mime, b64 = _encode_image(screenshot_path)
    prompt = _build_prompt(extracted, settings.blog_brand_name)

    async with httpx.AsyncClient(timeout=120.0) as client:
        res = await client.post(
            settings.groq_endpoint,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.groq_api_key}",
            },
            json={
                "model": settings.groq_vision_model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/{mime};base64,{b64}"},
                            },
                        ],
                    }
                ],
                "temperature": 0.6,
                "max_tokens": 4096,
                "response_format": {"type": "json_object"},
            },
        )

    if not res.is_success:
        raise RuntimeError(
            f"Groq Vision Error: {res.status_code} - {res.text[:500]}"
        )

    content = res.json()["choices"][0]["message"]["content"]
    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"IA retornou JSON inválido: {content[:300]}") from exc


def save_blog_markdown(post: dict[str, Any], settings: Settings) -> Path:
    settings.posts_path.mkdir(parents=True, exist_ok=True)
    ts = post.get("_saved_at") or datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe_title = "".join(
        c if c.isalnum() or c in " -_" else "" for c in post.get("titulo", "post")[:50]
    ).strip().replace(" ", "-").lower() or "post"
    path = settings.posts_path / f"{ts}_{safe_title}.md"

    tags = post.get("tags", [])
    tags_line = ", ".join(tags) if isinstance(tags, list) else str(tags)

    path.write_text(
        f"""---
title: {post.get('titulo', '')}
subtitle: {post.get('subtitulo', '')}
description: {post.get('meta_descricao', '')}
tags: [{tags_line}]
---

# {post.get('titulo', '')}

*{post.get('subtitulo', '')}*

{post.get('corpo_markdown', '')}

---

**{post.get('cta', '')}**
""",
        encoding="utf-8",
    )
    return path.resolve()
