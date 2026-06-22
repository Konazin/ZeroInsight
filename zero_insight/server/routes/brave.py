from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from zero_insight.config import Settings
from zero_insight.pipeline import test_cdp_sync
from zero_insight.services.brave_manager import BraveManager

router = APIRouter(tags=["brave"])
logger = logging.getLogger(__name__)


@router.post("/brave/start")
def brave_start() -> dict:
    try:
        manager = BraveManager(Settings.from_env())
        ok = manager.start_brave_with_cdp()
        return {"ok": ok, "message": "Brave iniciado para uso com CDP." if ok else "Brave não encontrado. Verifique se está instalado."}
    except Exception as exc:
        logger.exception("Falha ao iniciar Brave")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/brave/status")
def brave_status() -> dict:
    try:
        ok, message = test_cdp_sync(Settings.from_env())
        return {"ok": ok, "message": message}
    except Exception as exc:
        logger.warning("Erro ao verificar status do Brave: %s", exc)
        return {"ok": False, "message": f"Erro ao verificar CDP: {exc}"}
