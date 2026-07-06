from __future__ import annotations

import json
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import FileResponse

from zero_insight.brand.cache import brand_dir, load_brand_profile, save_brand_profile
from zero_insight.config import Settings
from zero_insight.server.schemas import BrandImportRequest
from zero_insight.server.security import GENERIC_ERROR_DETAIL, validate_identifier
from zero_insight.services import BrandService

router = APIRouter(tags=["brands"])
logger = logging.getLogger(__name__)

_SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc", ".png", ".jpg", ".jpeg", ".webp"}


@router.post("/brands/import")
def import_brand(request: BrandImportRequest) -> dict:
    path = Path(request.path.strip())
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Documento não encontrado: {path}")
    if path.suffix.lower() not in _SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=422,
            detail=f"Formato não suportado: {path.suffix}. Use: {', '.join(sorted(_SUPPORTED_EXTENSIONS))}",
        )
    try:
        profile, profile_path = BrandService(Settings.from_env()).import_document(
            path,
            brand_name=request.brand_name,
            use_external_ai=request.use_external_ai,
        )
        return {"id": profile_path.parent.name, "path": str(profile_path), "profile": profile.to_dict()}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Falha ao importar documento de marca: %s", path)
        raise HTTPException(status_code=500, detail="Falha ao importar a marca. Verifique o documento e os logs.") from exc


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
    brand_id = validate_identifier(brand_id, "brand_id")
    try:
        profile = load_brand_profile(brand_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail="Marca não encontrada.") from exc
    return profile.to_dict()


@router.put("/brands/{brand_id}")
def update_brand(brand_id: str, data: dict) -> dict:
    brand_id = validate_identifier(brand_id, "brand_id")
    try:
        profile = load_brand_profile(brand_id)
        merged = profile.to_dict()
        merged.update(data)
        from zero_insight.brand import BrandProfile

        saved = save_brand_profile(BrandProfile.from_dict(merged), brand_dir(brand_id))
        return {"ok": True, "path": str(saved)}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Falha ao atualizar marca: %s", brand_id)
        raise HTTPException(status_code=400, detail="Não foi possível atualizar a marca.") from exc


@router.post("/brands/{brand_id}/logo")
async def upload_brand_logo(brand_id: str, file: UploadFile) -> dict:
    brand_id = validate_identifier(brand_id, "brand_id")
    _ALLOWED = {".png", ".jpg", ".jpeg", ".webp"}
    suffix = Path(file.filename or "logo.png").suffix.lower()
    if suffix not in _ALLOWED:
        raise HTTPException(status_code=422, detail=f"Formato não suportado: {suffix}. Use PNG, JPG ou WEBP.")
    try:
        directory = brand_dir(brand_id)
        assets_dir = directory / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        logo_path = assets_dir / f"logo{suffix}"
        logo_path.write_bytes(await file.read())

        profile = load_brand_profile(brand_id)
        merged = profile.to_dict()
        merged.setdefault("assets", {})["logo_path"] = str(logo_path)
        from zero_insight.brand import BrandProfile
        save_brand_profile(BrandProfile.from_dict(merged), directory)
        return {"ok": True, "logo_path": str(logo_path)}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Falha ao salvar logo: %s", brand_id)
        raise HTTPException(status_code=500, detail=GENERIC_ERROR_DETAIL) from exc


@router.get("/brands/{brand_id}/logo")
def get_brand_logo(brand_id: str) -> FileResponse:
    brand_id = validate_identifier(brand_id, "brand_id")
    try:
        profile = load_brand_profile(brand_id)
        logo_path = (profile.assets or {}).get("logo_path", "")
        if not logo_path or not Path(logo_path).exists():
            raise HTTPException(status_code=404, detail="Logo não configurada para esta marca.")
        return FileResponse(logo_path)
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Falha ao servir logo de %s: %s", brand_id, exc)
        raise HTTPException(status_code=404, detail="Logo não encontrada.") from exc
