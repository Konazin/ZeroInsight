from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from zero_insight.config import Settings
from zero_insight.pipeline import test_cdp_sync, test_groq_sync
from zero_insight.services.brave_manager import BraveManager


@dataclass
class CheckResult:
    name: str
    status: str
    message: str
    action: str


class EnvironmentService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.brave = BraveManager(settings)

    def run_checks(self) -> list[CheckResult]:
        results: list[CheckResult] = []
        brave_path = self.brave.find_brave_executable()
        results.append(
            CheckResult(
                "Brave instalado",
                "OK" if brave_path else "ERROR",
                str(brave_path) if brave_path else "Brave nao encontrado.",
                "Instale pelo botao Instalar Brave ou pela pagina oficial.",
            )
        )

        cdp_ok, cdp_msg = test_cdp_sync(self.settings)
        results.append(
            CheckResult(
                "Brave/CDP",
                "OK" if cdp_ok else "WARNING",
                cdp_msg,
                "Inicie o Brave dedicado e faca login manual no Dino.",
            )
        )

        groq_ok, groq_msg = test_groq_sync(self.settings)
        results.append(
            CheckResult(
                "Groq API",
                "OK" if groq_ok else "ERROR",
                groq_msg,
                "Configure GROQ_API_KEY e confirme o modelo no .env.",
            )
        )

        results.extend(
            [
                self._dir_check("Posts", self.settings.posts_path),
                self._dir_check("Screenshots", self.settings.screenshots_path),
                self._dir_check("Stories", self.settings.stories_path),
            ]
        )
        return results

    @staticmethod
    def _dir_check(name: str, path: Path) -> CheckResult:
        try:
            path.mkdir(parents=True, exist_ok=True)
            return CheckResult(name, "OK", str(path), "Nenhuma acao necessaria.")
        except Exception as exc:
            return CheckResult(
                name,
                "ERROR",
                f"Nao foi possivel preparar {path}: {exc}",
                "Escolha um diretorio gravavel nas configuracoes.",
            )
