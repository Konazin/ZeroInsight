from __future__ import annotations

import json
import re
from typing import Any

from zero_insight.ai_providers.base import TextProvider


class MockTextProvider(TextProvider):
    name = "mock"

    def generate_text(self, prompt: str, system_prompt: str | None = None, temperature: float = 0.4) -> str:
        if "BrandProfile" in prompt or "brand_name" in prompt:
            return json.dumps(
                {
                    "brand_name": "Marca importada",
                    "summary": "Perfil gerado por mock provider para revisao humana.",
                    "tone_of_voice": ["claro", "institucional", "responsavel"],
                    "forbidden_terms": ["garantido", "sem risco"],
                    "preferred_terms": ["clareza", "seguranca", "analise"],
                    "visual_style": ["limpo", "moderno", "confiavel"],
                    "color_palette": [{"name": "Azul", "hex": "#2563EB", "usage": "acao"}],
                    "typography_notes": [],
                    "logo_usage_notes": [],
                    "layout_rules": ["manter area segura"],
                    "image_style_rules": ["sem texto embutido"],
                    "content_rules": ["evitar promessas absolutas"],
                    "compliance_rules": ["revisar antes de publicar"],
                    "target_audience": ["publico juridico"],
                    "cta_style": ["direto"],
                    "examples": [],
                },
                ensure_ascii=False,
            )
        return "Texto gerado pelo mock provider."

    def generate_json(
        self,
        prompt: str,
        schema_hint: dict[str, Any] | None = None,
        system_prompt: str | None = None,
    ) -> dict[str, Any]:
        if (schema_hint or {}).get("title") == "ZeroInsightStoryScript":
            match = re.search(r"Use exatamente (\d+) slides", prompt)
            count = max(1, int(match.group(1))) if match else 1
            return {
                "slides": [
                    {
                        "order": order,
                        "hook": "Informação clara para uma decisão segura",
                        "body": "Confira contexto, documentos e riscos antes de decidir.",
                        "cta": "Fale com nossa equipe",
                        "visual_idea": "composição institucional limpa",
                        "image_prompt": "visual jurídico moderno e confiável",
                        "compliance_notes": ["Não prometer resultados."],
                    }
                    for order in range(1, count + 1)
                ]
            }
        return super().generate_json(
            prompt,
            schema_hint=schema_hint,
            system_prompt=system_prompt,
        )
