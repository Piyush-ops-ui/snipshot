"""
Brand Kit schema for Institute styling, colors, typography, watermarks, and bumpers.
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field


class BrandKitConfig(BaseModel):
    id: str = Field(default="tech_summit_trainers", description="Unique brand identifier")
    name: str = Field(default="TechSummitTrainers Official", description="Human-readable brand name")
    
    # Color palette (Hex codes)
    primary_color: str = Field(default="#00F2FE", description="Cyan accent for keywords & progress")
    secondary_color: str = Field(default="#4FACFE", description="Secondary accent color")
    background_color: str = Field(default="#0F172A", description="Slate dark background")
    text_color: str = Field(default="#F8FAFC", description="High-contrast white text")
    accent_keyword_color: str = Field(default="#38BDF8", description="Color for technical keyword popups")
    
    # Typography
    font_family: str = Field(default="JetBrains Mono", description="Monospace font for code & captions")
    font_size_pt: int = Field(default=32, description="Base point size for caption text")
    
    # Watermarking & Badging
    watermark_text: Optional[str] = Field(default="TechSummitTrainers", description="Subtle corner/header text")
    logo_path: Optional[str] = Field(default=None, description="Path to institution logo PNG")
    logo_base64: Optional[str] = Field(default=None, description="Base64 encoded logo image data URL")
    logo_position: Literal["top_left", "top_right", "bottom_left", "bottom_right"] = "top_right"
    show_provenance_badge: bool = Field(default=True, description="Show glowing cyan badge on repaired technical terms")
    
    # Bumpers
    enable_intro_bumper: bool = Field(default=False, description="Whether to prepend intro bumper")
    intro_bumper_duration: float = Field(default=1.5, ge=0.0, le=5.0)
    enable_outro_bumper: bool = Field(default=True, description="Whether to append branded outro bumper")
    outro_bumper_duration: float = Field(default=2.0, ge=0.0, le=5.0)
