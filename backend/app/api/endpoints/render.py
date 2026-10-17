"""
Render Endpoints.
Triggers streaming Pillow + FFmpeg composition jobs and delivers 1080x1920 MP4 files.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pathlib import Path
import os
import uuid

from backend.app.schemas.api_requests import RenderReelRequest, RenderProgressResponse
from backend.app.core.compositor import ReelCompositor
from backend.app.config import settings

router = APIRouter()
compositor = ReelCompositor()


@router.post("/trigger", response_model=RenderProgressResponse)
async def trigger_render(request: RenderReelRequest, background_tasks: BackgroundTasks):
    """
    Renders Reel-IR timeline into a broadcast 1080x1920 MP4 video.
    """
    job_id = f"job_{uuid.uuid4().hex[:8]}"
    out_filename = request.output_filename or f"{request.reel_ir.reel_id}_rendered.mp4"
    output_path = settings.EXPORT_DIR / out_filename

    try:
        compositor.render(request.reel_ir, str(output_path))
        return RenderProgressResponse(
            job_id=job_id,
            status="complete",
            progress_percent=100.0,
            download_url=f"/api/render/download/{out_filename}",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rendering failed: {str(e)}")


@router.get("/download/{filename}")
async def download_rendered_mp4(filename: str):
    clean_name = os.path.basename(filename)
    mp4_path = settings.EXPORT_DIR / clean_name
    if not mp4_path.exists():
        raise HTTPException(status_code=404, detail="Rendered video not found")
    return FileResponse(str(mp4_path), media_type="video/mp4", filename=clean_name)
