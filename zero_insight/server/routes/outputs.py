from __future__ import annotations

import logging
import mimetypes
import os
import sys
import subprocess
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from zero_insight.config import PROJECT_ROOT, Settings
from zero_insight.server.security import safe_output_path
from zero_insight.services import OutputService

router = APIRouter(tags=["outputs"])
logger = logging.getLogger(__name__)

# Limite de tamanho para arquivos servidos inline (proteção contra leitura
# de arquivos gigantes em memória). Imagens de story ficam bem abaixo disso.
_MAX_SERVE_BYTES = 25 * 1024 * 1024  # 25 MB


def _item(kind: str, path: Path) -> dict | None:
    try:
        stat = path.stat()
        return {
            "type": kind,
            "name": path.name,
            "path": str(path),
            "modified_at": stat.st_mtime,
            "size": stat.st_size,
        }
    except OSError:
        logger.warning("Arquivo não acessível: %s", path)
        return None


@router.get("/outputs")
def outputs() -> list[dict]:
    service = OutputService(Settings.from_env())
    items: list[dict] = []
    for path in service.list_posts():
        item = _item("post", path)
        if item:
            items.append(item)
    for path in service.list_story_campaigns():
        item = _item("story", path)
        if item:
            items.append(item)
    return sorted(items, key=lambda item: item["modified_at"], reverse=True)


@router.get("/outputs/file")
def serve_file(path: str = Query(..., max_length=1024)) -> Response:
    """Serve um arquivo de saída (imagem, HTML) contido nas raízes permitidas.

    O caminho é validado para impedir acesso a arquivos fora dos diretórios
    de saída (ex.: `.env`, arquivos do sistema).
    """
    full = safe_output_path(path)
    if not full.exists() or not full.is_file():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado.")
    if full.stat().st_size > _MAX_SERVE_BYTES:
        raise HTTPException(status_code=413, detail="Arquivo grande demais para servir.")
    media_type, _ = mimetypes.guess_type(str(full))
    media_type = media_type or "application/octet-stream"
    return Response(content=full.read_bytes(), media_type=media_type)


@router.post("/outputs/open-folder")
def open_folder(path: str = Query(..., max_length=1024)) -> dict:
    """Abre uma pasta de saída no explorador de arquivos do sistema.

    Restrito às raízes de saída permitidas para não abrir/expor caminhos
    arbitrários do sistema.
    """
    full = safe_output_path(path)
    if not full.exists():
        raise HTTPException(status_code=404, detail="Pasta não encontrada.")
    target = str(full) if full.is_dir() else str(full.parent)
    try:
        if sys.platform == "win32":
            os.startfile(target)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", target])
        else:
            subprocess.Popen(["xdg-open", target])
        return {"ok": True}
    except Exception as exc:
        logger.warning("Não foi possível abrir a pasta: %s", exc)
        return {"ok": False, "detail": str(exc)}


@router.get("/logs")
def logs() -> list[str]:
    settings = Settings.from_env()
    candidates = [settings.output_path, PROJECT_ROOT / "results.jsonl"]
    for path in candidates:
        if path.exists():
            try:
                lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
                return [line for line in lines[-300:] if line.strip()]
            except OSError as exc:
                logger.warning("Falha ao ler logs de %s: %s", path, exc)
    return []

