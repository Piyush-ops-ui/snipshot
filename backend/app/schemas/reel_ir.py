"""
Canonical Reel-IR Schema (Unified 5-Track Intermediate Representation).
Unifies Mode A (Lecture Decompiler) and Mode B (Prompt Compiler).
"""

from enum import Enum
from typing import List, Optional, Tuple
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from backend.app.schemas.brand import BrandKitConfig


class LayoutMode(str, Enum):
    SINGLE_FOCUS = "single_focus"        # Stabilized dead-zone camera on active region
    SPLIT_STAGE = "split_stage"          # Upper IDE crop + Lower Terminal/Diagram crop
    CODE_SPOTLIGHT = "code_spotlight"    # Rendered AST syntax card + zoomed context


class TemplateArchetype(str, Enum):
    STANDARD_SPOTLIGHT = "standard_spotlight"  # Default clean single/split focus
    BUG_HUNTER = "bug_hunter"                  # Crimson red banner turning Emerald Green at error resolution
    VS_BATTLE = "vs_battle"                    # Top Legacy/Verbose vs Bottom Modern/Optimal card split
    PREDICT_OUTPUT = "predict_output"          # 2s freeze-frame callout asking audience to comment output


class RedactionBox(BaseModel):
    id: str = Field(..., description="Unique redaction identifier")
    start: float = Field(..., description="Start timestamp of secret visibility", ge=0.0)
    end: float = Field(..., description="End timestamp of secret visibility", ge=0.0)
    box: Tuple[int, int, int, int] = Field(..., description="[x, y, w, h] pixel bounding box on source frame")
    secret_type: str = Field(default="api_key", description="Type of detected secret (api_key, password, token, env_secret, pii)")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class SocialGrowthPack(BaseModel):
    hook_title: str = Field(..., description="Curiosity-inducing hook title for social captions")
    broad_hashtags: List[str] = Field(default_factory=list, description="Broad reach tags (e.g., #Coding #WebDev #Tech)")
    stack_hashtags: List[str] = Field(default_factory=list, description="Language/Framework tags (e.g., #React #SpringBoot)")
    micro_api_hashtags: List[str] = Field(default_factory=list, description="Exact API tags from screen tokens (e.g., #useEffect)")
    pinned_code_comment: str = Field(default="", description="Ready-to-paste comment with exact code snippet")
    qr_code_data: Optional[str] = Field(None, description="Data or URL encoded in the outro QR badge")


class WordAlignment(BaseModel):
    id: str = Field(..., description="Unique word identifier")
    word: str = Field(..., description="Displayed word text in captions")
    start: float = Field(..., description="Start timestamp in seconds from clip beginning", ge=0.0)
    end: float = Field(..., description="End timestamp in seconds from clip beginning", ge=0.0)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    is_technical: bool = Field(default=False, description="True if verified programming identifier")
    
    # Provenance data (if repaired via ScreenLex-ASR)
    raw_asr_word: Optional[str] = Field(None, description="Original ungrounded word from Whisper")
    provenance_frame_time: Optional[float] = Field(None, description="Source video timestamp where token was found on screen")
    provenance_bbox: Optional[Tuple[int, int, int, int]] = Field(None, description="[x, y, w, h] pixel bounding box on 1080p source")
    provenance_thumbnail_url: Optional[str] = Field(None, description="Relative URL to cropped image proof")
    phonetic_sim_score: Optional[float] = Field(None, description="Phonetic + surface similarity score (0.0 to 1.0)")


class ViewportKeyframe(BaseModel):
    timestamp: float = Field(..., description="Keyframe timestamp in seconds from clip beginning", ge=0.0)
    mode: LayoutMode = Field(default=LayoutMode.SINGLE_FOCUS)
    
    # Normalized coordinates [x, y, w, h] in range [0.0, 1.0] relative to 1920x1080 source frame
    top_crop: Tuple[float, float, float, float] = Field(
        ..., description="[x, y, w, h] normalized crop for upper/main viewport"
    )
    bottom_crop: Optional[Tuple[float, float, float, float]] = Field(
        None, description="[x, y, w, h] normalized crop for lower viewport (used in SplitStage mode)"
    )
    transition_duration: float = Field(default=0.0, description="Duration in seconds (0.0 = jump cut)", ge=0.0)


class CodeSpotlightCard(BaseModel):
    id: str = Field(..., description="Unique code card identifier")
    start: float = Field(..., description="Card display start timestamp in seconds", ge=0.0)
    end: float = Field(..., description="Card display end timestamp in seconds", ge=0.0)
    language: str = Field(default="python", description="Programming language for syntax highlighting")
    code: str = Field(..., description="Syntax-formatted code snippet")
    active_line_indices: List[int] = Field(default_factory=list, description="0-indexed lines to highlight")
    verified_by_ast: bool = Field(default=True, description="True if validated via Tree-sitter")


class ReelIR(BaseModel):
    schema_version: str = Field(default="1.0.0", description="Reel-IR version specification")
    reel_id: str = Field(..., description="Unique Reel identifier")
    mode: str = Field(..., description="'mode_a_extract' or 'mode_b_prompt'")
    title: str = Field(default="Untitled Reel")
    source_media_path: Optional[str] = Field(None, description="Absolute or relative path to source 16:9 video")
    
    # Temporal interval
    clip_start: float = Field(default=0.0, description="Start timestamp within source video (seconds)", ge=0.0)
    clip_end: float = Field(..., description="End timestamp within source video (seconds)", ge=0.0)
    total_duration: float = Field(..., description="Duration in seconds (clip_end - clip_start)", ge=0.0)
    
    # 5-Track Declarative Timeline
    audio_path: str = Field(..., description="Path to extracted or synthesized audio WAV")
    transcript: List[WordAlignment] = Field(default_factory=list, description="Word-level aligned transcript track")
    viewports: List[ViewportKeyframe] = Field(default_factory=list, description="Viewport retargeting track")
    code_cards: List[CodeSpotlightCard] = Field(default_factory=list, description="Readable916 overlay track")
    brand_kit: BrandKitConfig = Field(default_factory=BrandKitConfig)
    
    # Extensions: Security, Archetypes & Growth Pack
    template_archetype: TemplateArchetype = Field(default=TemplateArchetype.STANDARD_SPOTLIGHT)
    is_bug_to_fix_arc: bool = Field(default=False, description="True if video contains an error-to-resolution arc (Bug2Fix)")
    error_resolved_at: Optional[float] = Field(None, description="Timestamp where error switches to resolved Emerald Green (Bug Hunter)")
    redaction_boxes: List[RedactionBox] = Field(default_factory=list, description="Coordinates to blur for secrets and PII")
    social_growth_pack: Optional[SocialGrowthPack] = Field(None, description="Screen-grounded social growth pack & QR data")
    typing_hyperlapse_intervals: List[Tuple[float, float]] = Field(default_factory=list, description="Silent typing intervals > 1.2s sped up 2.5x")

    # Pedagogical Metadata & Provenance
    pedagogical_score: float = Field(default=0.0, description="Overall Pedagogical Triad Score")
    entry_closure_verified: bool = Field(default=True, description="False if clip starts on dangling deictic pronoun")
    exit_closure_verified: bool = Field(default=True, description="False if clip cuts off mid-sentence")
    technical_term_count: int = Field(default=0, description="Count of verified technical identifiers")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
