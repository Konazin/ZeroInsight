from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from zero_insight.brand.cache import brand_dir, load_brand_profile, save_brand_profile
from zero_insight.config import Settings
from zero_insight.server.schemas import BrandImportRequest
from zero_insight.services import BrandService

router = APIRouter(tags=["brands"])


@router.post("/brands/import")
def import_brand(request: BrandImportRequest) -> dict:
    path = Path(request.path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Documento nao encontrado.")
    profile, profile_path = BrandService(Settings.from_env()).import_document(
        path,
        brand_name=request.brand_name,
        use_external_ai=request.use_external_ai,
    )
    return {"id": profile_path.parent.name, "path": str(profile_path), "profile": profile.to_dict()}


@router.get("/brands")
def list_brands() -> list[dict]:
    service = BrandService(Settings.from_env())
    items = []
    for path in service.list_profiles():
        try:
            profile = json.loads(path.read_text(encoding="utf-8"))
            name = profile.get("brand_name") or path.parent.name
        except Exception:
            name = path.parent.name
        items.append({"id": path.parent.name, "name": name, "path": str(path)})
    return items


@router.get("/brands/{brand_id}")
def get_brand(brand_id: str) -> dict:
    try:
        profile = load_brand_profile(brand_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return profile.to_dict()


@router.put("/brands/{brand_id}")
def update_brand(brand_id: str, data: dict) -> dict:
    try:
        profile = load_brand_profile(brand_id)
        merged = profile.to_dict()
        merged.update(data)
        from zero_insight.brand import BrandProfile

        saved = save_brand_profile(BrandProfile.from_dict(merged), brand_dir(brand_id))
        return {"ok": True, "path": str(saved)}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
