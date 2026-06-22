from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException

from zero_insight.server.schemas.prompt import SavePromptRequest, UpdatePromptRequest

router = APIRouter(tags=["prompts"])
logger = logging.getLogger(__name__)


def _prompts_dir() -> Path:
    configured = os.getenv("ZEROINSIGHT_APP_DATA_DIR", "").strip()
    if configured:
        base = Path(configured).expanduser()
    else:
        raw = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA") or str(Path.home())
        base = Path(raw) / "ZeroInsight"
    d = base / "prompts"
    try:
        d.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        from zero_insight.config.settings import PROJECT_ROOT
        d = PROJECT_ROOT / ".zeroinsight_appdata" / "prompts"
        d.mkdir(parents=True, exist_ok=True)
    return d


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@router.get("/prompts")
def list_prompts() -> list[dict]:
    d = _prompts_dir()
    items = []
    for path in sorted(d.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            items.append(json.loads(path.read_text(encoding="utf-8")))
        except Exception:
            logger.warning("Falha ao ler template de prompt: %s", path)
    return items


@router.post("/prompts", status_code=201)
def create_prompt(request: SavePromptRequest) -> dict:
    if not request.name.strip():
        raise HTTPException(status_code=422, detail="O campo 'name' não pode ser vazio.")
    if not request.prompt.strip():
        raise HTTPException(status_code=422, detail="O campo 'prompt' não pode ser vazio.")
    template_id = str(uuid.uuid4())
    now = _now()
    data = {
        "id": template_id,
        "name": request.name.strip(),
        "prompt": request.prompt.strip(),
        "description": request.description.strip(),
        "brand_id": request.brand_id,
        "tags": request.tags,
        "created_at": now,
        "updated_at": now,
    }
    path = _prompts_dir() / f"{template_id}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


@router.get("/prompts/{template_id}")
def get_prompt(template_id: str) -> dict:
    path = _prompts_dir() / f"{template_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Template não encontrado.")
    return json.loads(path.read_text(encoding="utf-8"))


@router.put("/prompts/{template_id}")
def update_prompt(template_id: str, request: UpdatePromptRequest) -> dict:
    path = _prompts_dir() / f"{template_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Template não encontrado.")
    data = json.loads(path.read_text(encoding="utf-8"))
    if request.name is not None:
        data["name"] = request.name.strip()
    if request.prompt is not None:
        data["prompt"] = request.prompt.strip()
    if request.description is not None:
        data["description"] = request.description.strip()
    if request.brand_id is not None:
        data["brand_id"] = request.brand_id
    if request.tags is not None:
        data["tags"] = request.tags
    data["updated_at"] = _now()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


@router.delete("/prompts/{template_id}", status_code=204)
def delete_prompt(template_id: str) -> None:
    path = _prompts_dir() / f"{template_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Template não encontrado.")
    path.unlink()
