"""
Application Configuration settings using Pydantic BaseSettings.
"""

from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App Information
    APP_NAME: str = "SnipShot (Reel Studio)"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    
    # Server Binding
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173", "*"]

    # Base Paths (Calculated relative to project root)
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    UPLOAD_DIR: Path = BASE_DIR / "data" / "uploads"
    CACHE_DIR: Path = BASE_DIR / "data" / "cache"
    EXPORT_DIR: Path = BASE_DIR / "data" / "exports"
    DB_PATH: Path = BASE_DIR / "data" / "db" / "snipshot.db"
    DATA_DIR: Path = Path(__file__).resolve().parent / "data"
    FONTS_DIR: Path = DATA_DIR / "fonts"

    # Hardware Profile
    HARDWARE_PROFILE_OVERRIDE: Optional[str] = None  # None = auto-detect ("tier1", "tier2", "tier3")
    WHISPER_MODEL_SIZE: str = "small"
    WHISPER_COMPUTE_TYPE: str = "int8"
    WHISPER_CPU_THREADS: int = 12
    WHISPER_NUM_WORKERS: int = 2

    # Optional Cloud API Fallback Keys
    OPENAI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None


settings = Settings()

# Ensure runtime directories exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.CACHE_DIR.mkdir(parents=True, exist_ok=True)
settings.EXPORT_DIR.mkdir(parents=True, exist_ok=True)
settings.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
