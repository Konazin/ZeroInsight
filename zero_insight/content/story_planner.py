from __future__ import annotations

import json
from typing import Any

from zero_insight.content.story_script import StoryBrief, StorySlide
from zero_insight.brand.brand_profile import BrandProfile
from zero_insight.brand.cache import load_brand_profile
from zero_insight.ai_providers.base import ProviderError, TextProvider


def _clean_short(value: str, fallback: str, max_chars: int) -> str:
    cleaned = " ".join(value.replace("\n", " ").split()).strip(" .")
    if not cleaned:
        cleaned = fallback
    return cleaned[:max_chars].rsplit(" ", 1)[0].strip(" ,.;") if len(cleaned) > max_chars else cleaned


def _preferred_focus(profile: BrandProfile | None, company_summary: str) -> str:
    if company_summary:
        lowered = company_summary.lower()
        if "rpv" in lowered or "precatorio" in lowered or "precatório" in lowered:
            return "compra e venda de RPV e precatorios federais"
        return _clean_short(company_summary, "solucoes profissionais", 70)
    if profile and profile.summary:
        return _clean_short(profile.summary, "solucoes profissionais", 70)
    return "solucoes profissionais"


def _metric_summary(dino_data: dict[str, Any] | None) -> str:
    if not dino_data:
        return ""
    views = dino_data.get("visualizacoes")
    dist = dino_data.get("distribuicoes_realizadas")
    parts = []
    if views is not None:
        parts.append(f"{views} visualizacoes")
    if dist is not None:
        parts.append(f"{dist} distribuicoes")
    return " e ".join(parts)


def _load_profile(brief: StoryBrief) -> BrandProfile | None:
    target = brief.brand_profile_path or brief.brand_profile_id
    if not target:
        return None
    try:
        return load_brand_profile(target)
    except Exception:
        return None


STORY_SCRIPT_SCHEMA: dict[str, Any] = {
    "title": "ZeroInsightStoryScript",
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "slides": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "order": {"type": "integer"},
                    "hook": {"type": "string"},
                    "body": {"type": "string"},
                    "cta": {"type": "string"},
                    "visual_idea": {"type": "string"},
                    "image_prompt": {"type": "string"},
                    "compliance_notes": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": [
                    "order",
                    "hook",
                    "body",
                    "cta",
                    "visual_idea",
                    "image_prompt",
                    "compliance_notes",
                ],
            },
        }
    },
    "required": ["slides"],
}


def plan_story_script_with_provider(
    brief: StoryBrief,
    provider: TextProvider,
) -> list[StorySlide]:
    """Generate and validate a story script using the selected text provider."""
    profile = _load_profile(brief)
    prompt = f"""Gere um roteiro de Instagram Stories em português do Brasil.
Use exatamente {brief.slides} slides, numerados de 1 a {brief.slides}.
Mantenha hook, body e CTA curtos, claros e adequados a marketing jurídico.
Não faça promessas garantidas, não invente métricas e respeite as regras da marca.

Briefing:
{json.dumps(brief.to_dict(), ensure_ascii=False, indent=2)}

BrandProfile:
{json.dumps(profile.to_dict() if profile else {}, ensure_ascii=False, indent=2)}

Identificador da tarefa: story_script
"""
    data = provider.generate_json(
        prompt,
        schema_hint=STORY_SCRIPT_SCHEMA,
        system_prompt=(
            "Você cria roteiros institucionais verificáveis. "
            "Responda somente JSON válido no schema solicitado."
        ),
    )
    raw_slides = data.get("slides")
    if not isinstance(raw_slides, list) or len(raw_slides) != brief.slides:
        raise ProviderError(
            f"Provider retornou {len(raw_slides) if isinstance(raw_slides, list) else 0} "
            f"slides; esperado: {brief.slides}."
        )

    slides: list[StorySlide] = []
    for index, raw in enumerate(raw_slides, start=1):
        if not isinstance(raw, dict):
            raise ProviderError(f"Slide {index} retornado em formato inválido.")
        hook = str(raw.get("hook") or "").strip()
        body = str(raw.get("body") or "").strip()
        cta = str(raw.get("cta") or brief.cta or "").strip()
        if not hook or not body or not cta:
            raise ProviderError(f"Slide {index} retornou campos obrigatórios vazios.")
        visual_idea = str(raw.get("visual_idea") or "composição institucional limpa").strip()
        image_prompt = str(raw.get("image_prompt") or visual_idea).strip()
        notes = raw.get("compliance_notes")
        compliance_notes = (
            [str(note).strip() for note in notes if str(note).strip()]
            if isinstance(notes, list)
            else []
        )
        slides.append(
            StorySlide(
                order=index,
                hook=hook,
                body=body,
                cta=cta,
                visual_idea=visual_idea,
                image_prompt=image_prompt,
                compliance_notes=compliance_notes,
            )
        )
    return slides


def plan_story_script(brief: StoryBrief) -> list[StorySlide]:
    """Planner deterministico para o MVP, sem dependencia de API externa."""
    topic = brief.topic.strip() or "tema juridico"
    objective = brief.objective.strip() or "orientar com clareza"
    audience = brief.audience.strip() or "pessoas interessadas no assunto"
    tone = brief.tone.strip() or "claro e responsavel"
    cta = brief.cta.strip() or "Fale com a Requisite"
    company_summary = brief.company_summary.strip()
    metrics = _metric_summary(brief.dino_data)
    profile = _load_profile(brief)
    if profile:
        if profile.tone_of_voice:
            tone = ", ".join(profile.tone_of_voice[:3])
        if profile.cta_style and not brief.cta.strip():
            cta = profile.cta_style[0]

    slides: list[StorySlide] = []
    for order in range(1, max(1, brief.slides) + 1):
        if brief.source == "manual_story_post":
            focus = _preferred_focus(profile, company_summary)
            brand = profile.brand_name if profile else brief.topic
            if order == 1:
                hook = _clean_short(topic, f"Conheca {brand}", 42)
                body = _clean_short(focus, "Atendimento claro, seguro e especializado.", 86)
                visual = "Post visual de marca para Stories, com fundo abstrato profissional e area de texto curta"
            elif order == brief.slides:
                hook = "Analise com clareza"
                body = _clean_short(f"{brand} orienta cada etapa com comunicacao direta e responsavel.", focus, 88)
                visual = "Tela final visual, marca em destaque, chamada curta para contato"
            else:
                hook = "Decida com seguranca"
                body = _clean_short("Entenda valores, prazos e documentos antes de negociar.", focus, 84)
                visual = "Checklist minimalista sem texto embutido, composicao premium"
        elif order == 1:
            hook = f"Voce sabe como avaliar {topic}?"
            body = (
                f"Antes de decidir, entenda o contexto, os documentos e os riscos "
                f"envolvidos. O foco aqui e {objective}."
            )
            visual = "Capa limpa com titulo forte e detalhe juridico discreto"
        elif order == brief.slides:
            hook = "Quer analisar com mais seguranca?"
            body = (
                f"A {(profile.brand_name if profile else 'Requisite')} pode apoiar {audience} com uma leitura clara, "
                f"responsavel e sem promessas absolutas sobre {topic}."
            )
            visual = "Tela final com chamada para conversa e marca em destaque"
        elif metrics and order == 2:
            hook = "O que os dados indicam?"
            body = (
                f"O painel Dino registrou {metrics}. Esses sinais ajudam a orientar "
                f"o conteudo, mas nao substituem analise individual."
            )
            visual = "Card de metricas com numeros e legenda objetiva"
        else:
            hook = "Antes de aceitar uma proposta"
            body = (
                "Confira valor, titularidade, documentacao e andamento do processo. "
                f"Uma abordagem {tone} reduz decisoes precipitadas."
            )
            visual = "Checklist visual com itens de verificacao"

        slides.append(
            StorySlide(
                order=order,
                hook=hook,
                body=body,
                cta=cta,
                visual_idea=visual,
                image_prompt=(
                    f"Instagram Story 9:16 sobre {topic}; {visual}; "
                    f"empresa: {company_summary[:220] if company_summary else audience}; "
                    f"estilo da marca: {', '.join(profile.visual_style[:4]) if profile else 'juridico moderno'}; "
                    "estetica juridica moderna, alto contraste, sem texto embutido"
                ),
                compliance_notes=[
                    "Nao prometer resultado.",
                    "Nao sugerir dispensa de analise juridica individual.",
                    *(profile.compliance_rules[:2] if profile else []),
                ],
            )
        )
    return slides
