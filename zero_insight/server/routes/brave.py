from __future__ import annotations

from fastapi import APIRouter

from zero_insight.config import Settings
from zero_insight.pipeline import test_cdp_sync
from zero_insight.services.brave_manager import BraveManager

router = APIRouter(tags=["brave"])


@router.post("/brave/start")
def brave_start() -> dict:
    manager = BraveManager(Settings.from_env())
    ok = manager.start_brave_with_cdp()
    return {"ok": ok, "message": "Brave iniciado para uso com CDP." if ok else "Brave nao encontrado."}


@router.get("/brave/status")
def brave_status() -> dict:
    ok, message = test_cdp_sync(Settings.from_env())
    return {"ok": ok, "message": message}
