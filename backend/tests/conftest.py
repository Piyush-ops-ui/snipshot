"""
Pytest Fixtures for SnipShot Backend Test Suite.
"""

import pytest
import sys
from pathlib import Path

# Add project root to sys.path so 'backend.app' can be imported cleanly
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.app.schemas.tssg import ScreenToken, ASRWord, VisualDiffEvent
from backend.app.schemas.reel_ir import ReelIR, WordAlignment, ViewportKeyframe, LayoutMode
from backend.app.schemas.brand import BrandKitConfig


@pytest.fixture
def sample_screen_tokens():
    return [
        ScreenToken(
            id="st_1",
            text="useEffect",
            norm_text="useeffect",
            phonetic_code="USFK",
            bbox=(120, 180, 240, 32),
            normalized_bbox=(0.0625, 0.1667, 0.125, 0.0296),
            timestamp=14.2,
            is_identifier=True,
            token_type="camelCase",
        ),
        ScreenToken(
            id="st_2",
            text="@Autowired",
            norm_text="@autowired",
            phonetic_code="ATWRT",
            bbox=(120, 240, 280, 32),
            normalized_bbox=(0.0625, 0.2222, 0.1458, 0.0296),
            timestamp=14.5,
            is_identifier=True,
            token_type="annotation",
        ),
        ScreenToken(
            id="st_3",
            text="kubectl",
            norm_text="kubectl",
            phonetic_code="KBKTL",
            bbox=(1050, 650, 320, 28),
            normalized_bbox=(0.5469, 0.6019, 0.1667, 0.0259),
            timestamp=28.0,
            is_identifier=True,
            token_type="cli_cmd",
        ),
    ]


@pytest.fixture
def sample_asr_words():
    return [
        ASRWord(word="dekho", start=13.0, end=13.4, probability=0.95),
        ASRWord(word="jab", start=13.45, end=13.7, probability=0.92),
        ASRWord(word="hum", start=13.75, end=13.95, probability=0.94),
        ASRWord(word="use", start=14.0, end=14.25, probability=0.58),
        ASRWord(word="a", start=14.28, end=14.38, probability=0.52),
        ASRWord(word="fact", start=14.4, end=14.8, probability=0.56),
        ASRWord(word="mein", start=14.85, end=15.1, probability=0.95),
        ASRWord(word="auto", start=15.15, end=15.45, probability=0.62),
        ASRWord(word="wired", start=15.5, end=15.9, probability=0.60),
        ASRWord(word="ko", start=15.95, end=16.15, probability=0.96),
        ASRWord(word="call", start=16.2, end=16.5, probability=0.93),
        ASRWord(word="karte", start=16.55, end=16.85, probability=0.91),
        ASRWord(word="hain", start=16.9, end=17.15, probability=0.95),
    ]


@pytest.fixture
def sample_reel_ir():
    return ReelIR(
        schema_version="1.0.0",
        reel_id="test_reel_001",
        mode="mode_a_extract",
        title="Test Reel",
        clip_start=10.0,
        clip_end=45.0,
        total_duration=35.0,
        audio_path="test_audio.wav",
        transcript=[
            WordAlignment(id="w1", word="dekho", start=0.0, end=0.4, confidence=0.95),
            WordAlignment(id="w2", word="useEffect", start=0.5, end=1.2, confidence=0.95, is_technical=True),
        ],
        viewports=[
            ViewportKeyframe(
                timestamp=0.0,
                mode=LayoutMode.SINGLE_FOCUS,
                top_crop=(0.0, 0.0, 0.38, 1.0),
            )
        ],
        brand_kit=BrandKitConfig(),
    )
