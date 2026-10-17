"""
Timeline & Provenance Endpoints.
Handles Reel-IR updates, manual boundary overrides, and serving cropped OCR pixel proof images.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import os
import json

from backend.app.schemas.reel_ir import ReelIR
from backend.app.config import settings

router = APIRouter()


@router.post("/validate", response_model=ReelIR)
async def validate_timeline(reel: ReelIR):
    """Validates Reel-IR schema and recalculated durations."""
    reel.total_duration = round(max(1.0, reel.clip_end - reel.clip_start), 2)
    return reel


@router.get("/provenance/thumb/{filename}")
async def get_provenance_thumbnail(filename: str):
    """Serves cropped OCR pixel proof image for inspection in the Studio UI."""
    clean_name = os.path.basename(filename)
    thumb_path = settings.CACHE_DIR / "provenance" / clean_name
    if not thumb_path.exists():
        raise HTTPException(status_code=404, detail="Provenance image not found")
    return FileResponse(str(thumb_path), media_type="image/png")
