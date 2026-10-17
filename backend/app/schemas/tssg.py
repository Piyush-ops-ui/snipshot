"""
Time-Aligned Screen-Speech Graph (TSSG) Schemas.
Represents multimodal nodes (ScreenTokens, ASRWords, VisualDiffs, ASTBlocks) and temporal alignments.
"""

from typing import List, Optional, Tuple, Dict, Any
from pydantic import BaseModel, Field


class ScreenToken(BaseModel):
    id: str = Field(..., description="Unique token ID")
    text: str = Field(..., description="Original raw OCR text")
    norm_text: str = Field(..., description="Lowercased / normalized string for lookup")
    phonetic_code: str = Field(..., description="Double Metaphone phonetic signature")
    bbox: Tuple[int, int, int, int] = Field(..., description="[x, y, w, h] pixel bounding box on source frame")
    normalized_bbox: Tuple[float, float, float, float] = Field(
        ..., description="[x, y, w, h] normalized in [0.0, 1.0] relative to 1920x1080"
    )
    timestamp: float = Field(..., description="Timestamp in seconds where token appeared on screen")
    is_identifier: bool = Field(default=False, description="True if satisfies programming identifier heuristics")
    token_type: str = Field(default="word", description="'camelCase', 'decorator', 'cli_cmd', 'keyword', 'path'")
    provenance_crop_path: Optional[str] = Field(default=None, description="Path to 1080p cropped screenshot (data/cache/provenance/st_<id>.png)")
    provenance_crop_base64: Optional[str] = Field(default=None, description="Base64 encoded thumbnail preview")


class ASRWord(BaseModel):
    word: str
    start: float
    end: float
    probability: float = Field(default=1.0)
    phonetic_code: Optional[str] = None


class VisualDiffEvent(BaseModel):
    timestamp: float
    diff_magnitude: float = Field(..., description="Mean absolute difference across frames")
    is_plateau: bool = Field(default=False, description="True if screen stabilized after movement")
    active_regions: List[Tuple[int, int, int, int]] = Field(default_factory=list, description="Bounding boxes of pixel changes")


class TSSGGraph(BaseModel):
    video_id: str
    duration_seconds: float
    screen_tokens: List[ScreenToken] = Field(default_factory=list)
    asr_words: List[ASRWord] = Field(default_factory=list)
    diff_events: List[VisualDiffEvent] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def get_tokens_in_window(self, start: float, end: float) -> List[ScreenToken]:
        """Returns all screen tokens visible within [start, end]."""
        return [tok for tok in self.screen_tokens if start <= tok.timestamp <= end]

    def get_words_in_window(self, start: float, end: float) -> List[ASRWord]:
        """Returns all ASR words spoken within [start, end]."""
        return [w for w in self.asr_words if (w.start >= start and w.end <= end)]
