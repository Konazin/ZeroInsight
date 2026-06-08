from __future__ import annotations

from typing import Any

from zero_insight.content.story_script import StoryBrief, StorySlide
from zero_insight.brand.brand_profile import BrandProfile
from zero_insight.brand.cache import load_brand_profile


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


def plan_story_script(brief: StoryBrief) -> list[StorySlide]:
    """Planner deterministico para o MVP, sem dependencia de API externa."""
    topic = brief.topic.strip() or "tema juridico"
    objective = brief.objective.strip() or "orientar com clareza"
    audience = brief.audience.strip() or "pessoas interessadas no assunto"
    tone = brief.tone.strip() or "claro e responsavel"
    cta = brief.cta.strip() or "Fale com a Requisite"
    metrics = _metric_summary(brief.dino_data)
    profile = _load_profile(brief)
    if profile:
        if profile.tone_of_voice:
            tone = ", ".join(profile.tone_of_voice[:3])
        if profile.cta_style and not brief.cta.strip():
            cta = profile.cta_style[0]

    slides: list[StorySlide] = []
    for order in range(1, max(1, brief.slides) + 1):
        if order == 1:
            hook = f"Voce sabe como avaliar {topic}?"
            body = (
                f"Antes de decidir, entenda o contexto, os documentos e os riscos "
                f"envolvidos. O foco aqui e {objective}."
            )
            if profile and profile.preferred_terms:
                body = f"{body} Use uma abordagem com {profile.preferred_terms[0]}."
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
