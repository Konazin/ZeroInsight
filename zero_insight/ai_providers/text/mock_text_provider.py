from __future__ import annotations

import json

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
