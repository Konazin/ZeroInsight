from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from zero_insight.brand.brand_profile import BrandProfile

DANGEROUS_ABSOLUTES = ("garantido", "100% aprovado", "sem risco", "dinheiro imediato garantido")


class BrandValidator:
    def validate_content(self, text: str, profile: BrandProfile | None) -> dict[str, Any]:
        warnings: list[str] = []
        errors: list[str] = []
        lowered = text.lower()
        for term in DANGEROUS_ABSOLUTES:
            if term in lowered:
                errors.append(f"Promessa absoluta perigosa: {term}")
        if profile:
            for term in profile.forbidden_terms:
                if term and term.lower() in lowered:
                    errors.append(f"Termo proibido pela marca: {term}")
            if profile.cta_style and "fale" not in lowered and "contato" not in lowered:
                warnings.append("CTA pode nao refletir o estilo preferido da marca.")
        if len(text) > 900:
            warnings.append("Texto longo para Story; revisar densidade.")
        return {
            "status": "FAIL" if errors else ("WARNING" if warnings else "PASS"),
            "warnings": warnings,
            "errors": errors,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

    def validate_profile(self, profile: BrandProfile) -> dict[str, Any]:
        warnings: list[str] = []
        errors: list[str] = []
        if not profile.brand_name or profile.brand_name == "Marca sem nome":
            warnings.append("Nome da marca precisa de revisao.")
        if not profile.color_palette:
            warnings.append("Paleta de cores nao identificada.")
        if not profile.tone_of_voice:
            warnings.append("Tom de voz nao identificado.")
        return {
            "status": "FAIL" if errors else ("WARNING" if warnings else "PASS"),
            "warnings": warnings,
            "errors": errors,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }
