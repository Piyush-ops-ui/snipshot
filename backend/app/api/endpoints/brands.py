"""
Brand Kit Endpoints.
Manages institute branding presets (colors, fonts, watermarks, intro/outro bumpers).
"""

from fastapi import APIRouter
from typing import List
import json

from backend.app.schemas.brand import BrandKitConfig
from backend.app.config import settings

router = APIRouter()


@router.get("/", response_model=List[BrandKitConfig])
async def list_brand_kits():
    """Lists all available institute Brand Kits."""
    path = settings.DATA_DIR / "default_brand_kits.json"
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                kits = json.load(f)
                return [BrandKitConfig(**k) for k in kits]
        except Exception:
            pass
    return [BrandKitConfig()]
