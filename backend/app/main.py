"""
SnipShot (Reel Studio) FastAPI Main Application Entrypoint.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from backend.app.config import settings
from backend.app.api.router import api_router
from backend.app.services.hardware_profiler import detect_hardware_profile

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("snipshot")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown hooks."""
    hw = detect_hardware_profile(settings.HARDWARE_PROFILE_OVERRIDE)
    logger.info("=" * 60)
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Hardware Profile: {hw.tier.upper()}")
    logger.info(f"Total RAM: {hw.total_ram_gb:.1f} GB (Available: {hw.available_ram_gb:.1f} GB) | CPU Cores: {hw.cpu_cores}")
    logger.info(f"CUDA Available: {hw.has_cuda} ({hw.gpu_name or 'CPU Mode'})")
    logger.info(f"Recommended Config: Whisper={hw.recommended_whisper_model} ({hw.recommended_whisper_compute}) | Encoder={hw.recommended_encoder}")
    logger.info("=" * 60)
    yield
    logger.info("Shutting down SnipShot backend engine.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Screen-Grounded Pedagogical Compilation (SGPC) Video Studio Engine",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from pathlib import Path
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, Dict, Any

from backend.app.api.endpoints import mode_a, mode_b, telemetry

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
OUTPUTS_DIR = ROOT_DIR / "backend" / "outputs"
PROVENANCE_DIR = ROOT_DIR / "data" / "cache" / "provenance"

# Ensure directories exist
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
PROVENANCE_DIR.mkdir(parents=True, exist_ok=True)

# API Routes
app.include_router(mode_a.router, prefix="/api/v1/mode-a", tags=["Mode A: Lecture Decompiler"])
app.include_router(mode_b.router, prefix="/api/v1/mode-b", tags=["Mode B: Prompt Explainer"])
app.include_router(telemetry.router, prefix="/api/v1/telemetry", tags=["Weapon 9: Telemetry & Bandit"])
app.include_router(api_router, prefix="/api")

# Static File Mounts for real 1080x1920 MP4 outputs & OCR provenance crops
app.mount("/outputs", StaticFiles(directory=str(ROOT_DIR / "backend" / "outputs")), name="outputs")
app.mount("/provenance", StaticFiles(directory=str(ROOT_DIR / "data" / "cache" / "provenance")), name="provenance")




@app.get("/health", tags=["System"])
async def health_check():
    """Healthcheck endpoint returning system state and hardware tier."""
    hw = detect_hardware_profile(settings.HARDWARE_PROFILE_OVERRIDE)
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "hardware_profile": hw.to_dict(),
    }


# Single-Origin Production Serving: Mount compiled Vite React frontend if frontend/dist exists
frontend_dist = ROOT_DIR / "frontend" / "dist"
if frontend_dist.exists() and (frontend_dist / "index.html").exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
