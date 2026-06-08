from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from zero_insight.ai_providers.base import TextProvider
from zero_insight.brand.brand_assets import find_first_logo
from zero_insight.brand.brand_profile import BrandProfile
from zero_insight.brand.brand_prompt_builder import BRAND_EXTRACTION_SYSTEM_PROMPT, build_brand_extraction_prompt
from zero_insight.brand.document_loader import LoadedBrandDocument


class BrandExtractor:
    def __init__(self, text_provider: TextProvider | None = None) -> None:
        self.text_provider = text_provider

    def extract(
        self,
        document: LoadedBrandDocument,
        brand_name: str | None = None,
        assets_dir: Path | None = None,
        allow_external_ai: bool = False,
    ) -> BrandProfile:
        if self.text_provider and allow_external_ai:
            try:
                prompt = build_brand_extraction_prompt(document.text)
                data = self.text_provider.generate_json(prompt, system_prompt=BRAND_EXTRACTION_SYSTEM_PROMPT)
                return self._profile_from_ai(data, document, brand_name, assets_dir)
            except Exception:
                pass
        return self._heuristic_profile(document, brand_name, assets_dir)

    def _profile_from_ai(
        self,
        data: dict,
        document: LoadedBrandDocument,
        brand_name: str | None,
        assets_dir: Path | None,
    ) -> BrandProfile:
        data["brand_name"] = brand_name or data.get("brand_name") or self._guess_brand_name(document.text)
        data["source_document_path"] = str(document.path)
        data["created_at"] = datetime.now(timezone.utc).isoformat()
        data["raw_extracted_text_excerpt"] = document.text[:2000]
        data["status"] = "needs_review"
        profile = BrandProfile.from_dict(data)
        logo = find_first_logo(assets_dir) if assets_dir else None
        if logo:
            profile.assets["logo_path"] = str(logo)
        return profile

    def _heuristic_profile(
        self,
        document: LoadedBrandDocument,
        brand_name: str | None,
        assets_dir: Path | None,
    ) -> BrandProfile:
        text = document.text
        colors = sorted(set(re.findall(r"#[0-9A-Fa-f]{6}\b", text)))
        words = re.findall(r"\b[A-Za-zÀ-ÿ]{4,}\b", text.lower())
        forbidden_terms = self._forbidden_terms(text)
        forbidden_words = {word for term in forbidden_terms for word in re.findall(r"\b[A-Za-zÀ-ÿ]{4,}\b", term.lower())}
        common = [
            word
            for word, _ in Counter(words).most_common(18)
            if word not in forbidden_words and word not in {"nao", "não", "usar", "sem"}
        ]
        lowered = text.lower()
        profile = BrandProfile(
            brand_name=brand_name or self._guess_brand_name(text),
            source_document_path=str(document.path),
            created_at=datetime.now(timezone.utc).isoformat(),
            summary=self._summary(text),
            tone_of_voice=self._lines_for(lowered, ["tom", "voz", "linguagem"]) or ["claro", "institucional"],
            forbidden_terms=forbidden_terms or self._lines_for(lowered, ["nao usar", "não usar", "evitar", "proibido"]),
            preferred_terms=common[:8],
            visual_style=self._lines_for(lowered, ["visual", "estilo", "imagem"]) or ["limpo", "moderno"],
            color_palette=[{"name": f"Cor {i + 1}", "hex": color.upper(), "usage": "identificada no documento"} for i, color in enumerate(colors)],
            typography_notes=self._lines_for(lowered, ["tipografia", "fonte", "font"]),
            logo_usage_notes=self._lines_for(lowered, ["logo", "marca", "logotipo"]),
            layout_rules=self._lines_for(lowered, ["layout", "margem", "grid", "espaco", "espaço"]),
            image_style_rules=self._lines_for(lowered, ["foto", "imagem", "ilustracao", "ilustração"]),
            content_rules=self._lines_for(lowered, ["conteudo", "conteúdo", "copy", "texto"]),
            compliance_rules=["Nao prometer resultados absolutos.", "Revisar comunicacao juridica antes de publicar."],
            target_audience=self._lines_for(lowered, ["publico", "público", "audiencia", "audiência"]),
            cta_style=self._lines_for(lowered, ["cta", "chamada", "contato"]) or ["claro e direto"],
            examples=[],
            raw_extracted_text_excerpt=text[:2000],
            status="needs_review",
        )
        logo = find_first_logo(assets_dir) if assets_dir else None
        if logo:
            profile.assets["logo_path"] = str(logo)
        return profile

    @staticmethod
    def _guess_brand_name(text: str) -> str:
        for line in text.splitlines():
            cleaned = line.strip()
            if 2 <= len(cleaned) <= 60 and not cleaned.endswith("."):
                return cleaned
        return "Marca sem nome"

    @staticmethod
    def _summary(text: str) -> str:
        compact = " ".join(text.split())
        return compact[:400] if compact else "Documento sem texto extraivel; revisar manualmente."

    @staticmethod
    def _lines_for(lowered_text: str, needles: list[str]) -> list[str]:
        results: list[str] = []
        for line in lowered_text.splitlines():
            cleaned = line.strip(" -\t")
            if len(cleaned) < 8:
                continue
            if any(needle in cleaned for needle in needles):
                results.append(cleaned[:180])
            if len(results) >= 6:
                break
        return results

    @staticmethod
    def _forbidden_terms(text: str) -> list[str]:
        terms: list[str] = []
        for line in text.splitlines():
            lowered = line.lower()
            if any(marker in lowered for marker in ("nao usar", "não usar", "evitar", "proibido")):
                payload = re.split(r":|-", line, maxsplit=1)
                raw = payload[1] if len(payload) > 1 else line
                for piece in re.split(r",|;|\.", raw):
                    cleaned = piece.strip(" -\t").lower()
                    if cleaned and cleaned not in {"nao usar", "não usar", "evitar", "proibido"}:
                        terms.append(cleaned)
        return terms
