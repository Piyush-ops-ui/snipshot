"""
API Request and Response Models.
"""

from typing import List, Optional
from pydantic import BaseModel, Field

from backend.app.schemas.reel_ir import ReelIR
from backend.app.schemas.brand import BrandKitConfig


class AnalyzeLectureResponse(BaseModel):
    video_id: str
    duration_seconds: float
    plateau_frames_count: int
    extracted_tokens_count: int
    candidate_clips: List[ReelIR] = Field(default_factory=list)


class GenerateExplainerRequest(BaseModel):
    prompt: str = Field(..., description="Educational topic prompt (e.g. 'JSON vs XML')")
    target_duration: float = Field(default=45.0, ge=15.0, le=90.0)
    brand_kit_id: str = Field(default="tech_summit_trainers")
    voice_id: str = Field(default="kokoro_neutral_teacher")


class RenderReelRequest(BaseModel):
    reel_ir: ReelIR
    output_filename: Optional[str] = None
    hardware_acceleration: bool = True


class RenderProgressResponse(BaseModel):
    job_id: str
    status: str = Field(..., description="'queued', 'rendering', 'complete', 'failed'")
    progress_percent: float = Field(default=0.0, ge=0.0, le=100.0)
    current_frame: int = 0
    total_frames: int = 0
    eta_seconds: float = 0.0
    download_url: Optional[str] = None
    error_message: Optional[str] = None


class TelemetryFeedbackRequest(BaseModel):
    reel_id: str
    retention_at_3s: float = Field(..., ge=0.0, le=1.0)
    completion_rate: float = Field(..., ge=0.0, le=1.0)
    click_through_rate: Optional[float] = None
