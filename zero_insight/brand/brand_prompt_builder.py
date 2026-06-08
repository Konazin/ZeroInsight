from __future__ import annotations

import json

from zero_insight.brand.brand_profile import BrandProfile


BRAND_EXTRACTION_SYSTEM_PROMPT = (
    "Voce e um especialista em branding, comunicacao visual e social media. "
    "Extraia diretrizes objetivas de comunicacao visual. Responda apenas JSON valido."
)


def build_brand_extraction_prompt(text: str) -> str:
    excerpt = text[:12000]
    return f"""Abaixo esta o texto extraido de um manual/documento de comunicacao visual.
Gere um BrandProfile com campos:
brand_name, summary, tone_of_voice, forbidden_terms, preferred_terms, visual_style,
color_palette, typography_notes, logo_usage_notes, layout_rules, image_style_rules,
content_rules, compliance_rules, target_audience, cta_style, examples.

Regras:
- Nao invente informacoes ausentes.
- Se algo nao estiver explicito, use lista vazia ou marque como "nao identificado".
- Se encontrar cores hex, preserve.
- Se encontrar nomes de fontes, preserve.
- Se houver regras de uso incorreto, coloque em forbidden_terms ou layout_rules.
- Responda apenas JSON.

Texto extraido:
{excerpt}
"""


def build_story_copy_prompt(
    topic: str,
    objective: str,
    audience: str,
    cta: str,
    slides: int,
    brand_profile: BrandProfile,
) -> str:
    return f"""Tema:
{topic}

Objetivo:
{objective}

Publico:
{audience}

CTA:
{cta}

BrandProfile:
{json.dumps(brand_profile.to_dict(), ensure_ascii=False, indent=2)}

Gere {slides} stories em JSON.
Cada story deve ter:
order, hook, body, cta, visual_idea, image_prompt, compliance_notes.

Regras:
- Nao use termos proibidos.
- Nao prometa resultado garantido.
- Nao use linguagem sensacionalista.
- Nao invente dados juridicos.
- Texto do Story deve ser curto.
- CTA deve ser claro.
- O image_prompt deve orientar apenas imagem/fundo/ilustracao, sem texto embutido.
- Responda apenas JSON.
"""


def build_image_prompt(topic: str, visual_idea: str, brand_profile: BrandProfile) -> str:
    return f"""Gerar imagem base para Instagram Story 9:16.
A imagem sera usada como fundo/visual principal, sem texto embutido.
Estilo da marca:
{", ".join(brand_profile.visual_style)}
Cores preferenciais:
{json.dumps(brand_profile.color_palette, ensure_ascii=False)}
Tema:
{topic}
Ideia visual:
{visual_idea}
Regras:
- Nao inserir texto.
- Nao inserir logotipo ficticio.
- Nao inserir marcas falsas.
- Evitar elementos poluidos.
- Composicao limpa com espaco livre para texto.
- Visual institucional, confiavel e moderno.
"""
