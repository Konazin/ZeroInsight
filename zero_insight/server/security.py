"""Utilitários de segurança compartilhados pelas rotas do servidor.

Centraliza:
  - contenção de caminhos (proteção contra path traversal / LFI);
  - validação de identificadores usados em caminhos de arquivo;
  - headers de segurança HTTP;
  - saneamento de mensagens de erro expostas ao cliente.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path

from fastapi import HTTPException

logger = logging.getLogger(__name__)

# Mensagem genérica retornada ao cliente para erros 500 — evita vazar
# stack traces, caminhos internos ou detalhes de configuração.
GENERIC_ERROR_DETAIL = "Erro interno ao processar a requisição. Verifique os logs do servidor."

# Identificadores seguros para uso em caminhos (brand_id, template, etc.):
# apenas letras, números, hífen, underscore e ponto — sem separadores nem "..".
_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")


def allowed_output_roots() -> list[Path]:
    """Diretórios cujos arquivos podem ser servidos/abertos publicamente.

    Qualquer caminho fora dessas raízes é rejeitado. Inclui as pastas de
    saída (stories, posts, screenshots) e o diretório de dados da marca.
    """
    from zero_insight.config import PROJECT_ROOT, Settings

    settings = Settings.from_env()
    # IMPORTANTE: apenas subdiretórios específicos de saída — nunca a raiz do
    # projeto ou o diretório-base de dados (que contêm .env, código-fonte, etc.).
    roots: list[Path] = []
    for candidate in (
        settings.stories_path,
        settings.posts_path,
        settings.screenshots_path,
        PROJECT_ROOT / "stories",
        PROJECT_ROOT / "posts",
        PROJECT_ROOT / "screenshots",
    ):
        try:
            roots.append(candidate.resolve())
        except (OSError, RuntimeError):
            continue

    # Diretório de dados da marca (logos, assets), se acessível.
    try:
        from zero_insight.brand.cache import brand_root, fallback_brand_root

        roots.append(brand_root().resolve())
        roots.append(fallback_brand_root().resolve())
    except Exception:  # pragma: no cover - best effort
        pass

    # Remove duplicatas preservando ordem.
    unique: list[Path] = []
    for root in roots:
        if root not in unique:
            unique.append(root)
    return unique


def is_within(base: Path, target: Path) -> bool:
    """True se `target` está contido em `base` (ambos já resolvidos)."""
    try:
        target.relative_to(base)
        return True
    except ValueError:
        return False


def safe_output_path(raw: str) -> Path:
    """Resolve um caminho de saída solicitado pelo cliente, garantindo que
    ele esteja contido em uma das raízes permitidas.

    Levanta HTTPException(403) para tentativas de traversal e HTTPException(400)
    para entradas inválidas.
    """
    if not raw or not raw.strip():
        raise HTTPException(status_code=400, detail="Caminho não informado.")

    # Rejeita explicitamente NUL e caracteres de controle.
    if "\x00" in raw:
        raise HTTPException(status_code=400, detail="Caminho inválido.")

    candidate = Path(raw)
    roots = allowed_output_roots()

    try:
        if candidate.is_absolute():
            resolved = candidate.resolve()
        else:
            # Resolve relativo a cada raiz permitida até encontrar contido.
            resolved = None
            for root in roots:
                probe = (root / candidate).resolve()
                if is_within(root, probe):
                    resolved = probe
                    break
            if resolved is None:
                resolved = candidate.resolve()
    except (OSError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail="Caminho inválido.") from exc

    if not any(is_within(root, resolved) for root in roots):
        logger.warning("Bloqueado acesso a caminho fora das raízes permitidas: %s", raw)
        raise HTTPException(status_code=403, detail="Acesso negado a esse caminho.")

    return resolved


def validate_identifier(value: str, field: str = "identificador") -> str:
    """Valida um identificador usado em caminho de arquivo. Bloqueia
    separadores de diretório e sequências de traversal."""
    value = (value or "").strip()
    if not value or not _SAFE_ID_RE.match(value) or value in {".", ".."}:
        raise HTTPException(status_code=400, detail=f"{field} inválido.")
    return value


# ── Middleware de headers de segurança ─────────────────────────────────────────

async def security_headers_middleware(request, call_next):
    """Adiciona headers de segurança a todas as respostas."""
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("X-Permitted-Cross-Domain-Policies", "none")
    response.headers.setdefault(
        "Permissions-Policy", "geolocation=(), microphone=(), camera=()"
    )
    return response
