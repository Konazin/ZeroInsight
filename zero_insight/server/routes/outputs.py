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
from zero_insight.services import OutputService

router = APIRouter(tags=["outputs"])
logger = logging.getLogger(__name__)


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


def _resolve_output_path(path: str) -> Path:
    full = Path(path)
    if full.is_absolute():
        return full
    return (PROJECT_ROOT / path).resolve()


@router.get("/outputs/file")
def serve_file(path: str = Query(...)) -> Response:
    """Serve um arquivo de saída (imagem, HTML) pelo caminho relativo ou absoluto."""
    full = _resolve_output_path(path)
    if not full.exists() or not full.is_file():
        raise HTTPException(status_code=404, detail=f"Arquivo não encontrado: {path}")
    media_type, _ = mimetypes.guess_type(str(full))
    media_type = media_type or "application/octet-stream"
    return Response(content=full.read_bytes(), media_type=media_type)


@router.post("/outputs/open-folder")
def open_folder(path: str = Query(...)) -> dict:
    """Abre uma pasta no explorador de arquivos do sistema operacional."""
    full = _resolve_output_path(path)
    if not full.exists():
        raise HTTPException(status_code=404, detail=f"Pasta não encontrada: {path}")
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

