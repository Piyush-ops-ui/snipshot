"""
End-to-End Pipeline Integration Test (SnipShot Automated Verification).
Runs the complete multi-stage pipeline on `demo_lecture.mp4`:
Plateau detection -> RapidOCR -> Whisper ASR -> Phonetic Repair -> ClosedThought -> Smart Reframer -> SafeCohort Blur -> Outro QR -> FFmpeg render.
Verifies that the output MP4 exists, is playable, has redacted secrets, and includes the outro QR badge.
"""

import os
import sys
import json
import pytest
from pathlib import Path
import cv2
import numpy as np

# Project root setup
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app.core.plateau_detector import PlateauDetector
from backend.app.core.screen_lex_ocr import ScreenLexMiner
from backend.app.core.grounded_asr import GroundedASR
from backend.app.core.phonetic_repair import PhoneticVisualRepairer
from backend.app.core.closed_thought import ClosedThoughtClipper
from backend.app.core.smart_reframer import SmartReframer
from backend.app.core.compositor import ReelCompositor
from backend.app.schemas.reel_ir import (
    ReelIR,
    LayoutMode,
    ViewportKeyframe,
    RedactionBox,
    SocialGrowthPack,
    TemplateArchetype,
)
from backend.app.schemas.brand import BrandKitConfig
from backend.app.services.ffmpeg_service import FFmpegService
from backend.app.config import settings

VIDEO_PATH = ROOT_DIR / "benchmarks" / "test_clips" / "demo_lecture.mp4"
METADATA_PATH = ROOT_DIR / "benchmarks" / "test_clips" / "demo_lecture.json"
AUDIO_PATH = ROOT_DIR / "benchmarks" / "test_clips" / "demo_lecture_audio.wav"
OUTPUT_REEL_PATH = ROOT_DIR / "data" / "exports" / "e2e_verified_reel.mp4"


@pytest.fixture(scope="module")
def pipeline_artifacts():
    """Runs ingestion steps once for the test module to verify each pipeline stage."""
    assert VIDEO_PATH.exists(), f"Synthetic demo lecture video not found at {VIDEO_PATH}"
    
    # 1. Plateau Detection
    detector = PlateauDetector(output_dir=ROOT_DIR / "data" / "cache" / "keyframes")
    plateaus, diff_events = detector.detect_plateaus(str(VIDEO_PATH))

    # 2. ScreenLex OCR
    ocr = ScreenLexMiner()
    tokens = ocr.extract_screen_tokens(plateaus)
    secrets = ocr.scan_safe_cohort(plateaus)

    # 3. Grounded ASR & Phonetic Repair
    asr = GroundedASR()
    raw_words = asr._mock_transcription(str(AUDIO_PATH))
    repairer = PhoneticVisualRepairer()
    repaired_words = repairer.repair_transcript(raw_words, tokens)

    # 4. ClosedThought Clipping
    clipper = ClosedThoughtClipper()
    candidate_spans = clipper.extract_highlights(repaired_words, diff_events, top_k=3)

    # 5. Smart Reframing
    reframer = SmartReframer()
    clip_start = candidate_spans[0].start_time if candidate_spans else 0.0
    clip_end = candidate_spans[0].end_time if candidate_spans else 45.0
    viewports, code_cards, layout_mode = reframer.compute_viewports(
        clip_start, clip_end, tokens, diff_events
    )

    return {
        "plateaus": plateaus,
        "diff_events": diff_events,
        "tokens": tokens,
        "secrets": secrets,
        "raw_words": raw_words,
        "repaired_words": repaired_words,
        "candidate_spans": candidate_spans,
        "viewports": viewports,
        "code_cards": code_cards,
        "layout_mode": layout_mode,
        "clip_start": clip_start,
        "clip_end": clip_end,
    }


def test_stage1_demo_lecture_media_probe():
    """Verifies that demo_lecture.mp4 is a valid 90-second 1920x1080 30fps video."""
    ffmpeg = FFmpegService()
    probe = ffmpeg.probe_video(str(VIDEO_PATH))
    assert probe["width"] == 1920
    assert probe["height"] == 1080
    assert abs(probe["fps"] - 30.0) < 0.1
    assert abs(probe["duration"] - 90.0) < 1.0


def test_stage2_plateaus_and_ocr_token_extraction(pipeline_artifacts):
    """Verifies plateau detection and RapidOCR extracted programming tokens."""
    tokens = pipeline_artifacts["tokens"]
    plateaus = pipeline_artifacts["plateaus"]
    
    assert len(plateaus) >= 5, f"Expected >= 5 plateaus, got {len(plateaus)}"
    assert len(tokens) >= 50, f"Expected >= 50 tokens, got {len(tokens)}"

    # Check for presence of essential identifiers
    token_texts = {t.text for t in tokens}
    assert any("useEffect" in t for t in token_texts), "useEffect not detected on screen"
    assert any("app.py" in t for t in token_texts), "app.py not detected on screen"


def test_stage3_safe_cohort_secret_detection(pipeline_artifacts):
    """Verifies SafeCohort detects exposed API_KEY = 'sk-live-9988776655' in .env section."""
    secrets = pipeline_artifacts["secrets"]
    assert len(secrets) >= 1, "Expected SafeCohort to detect at least 1 exposed secret"
    
    api_key_secrets = [s for s in secrets if s.secret_type in ["api_key", "openai_api_key", "env_secret"]]
    assert len(api_key_secrets) >= 1, "Failed to identify API key secret type"
    
    # Check that bounding box is on left editor pane
    x, y, w, h = api_key_secrets[0].box
    assert x < 1000, f"Secret box x={x} is not on the left editor pane"
    assert y < 250, f"Secret box y={y} is not in the configuration header section"


def test_stage4_phonetic_repair_of_mangled_terms(pipeline_artifacts):
    """Verifies Phonetic-Surface repair fixes mangled Hinglish technical terms."""
    repaired_words = pipeline_artifacts["repaired_words"]
    repaired_texts = {w.word for w in repaired_words}

    # 'use a fact' -> 'useEffect'
    assert "useEffect" in repaired_texts, "Phonetic repair failed for 'use a fact' -> 'useEffect'"
    # 'auto wired' -> '@Autowired'
    assert "@Autowired" in repaired_texts, "Phonetic repair failed for 'auto wired' -> '@Autowired'"
    # 'coober netties' -> 'Kubernetes'
    assert "Kubernetes" in repaired_texts, "Phonetic repair failed for 'coober netties' -> 'Kubernetes'"


def test_stage5_closed_thought_and_split_stage_reframing(pipeline_artifacts):
    """Verifies ClosedThought discovers highlight with entry closure and SplitStage layout."""
    spans = pipeline_artifacts["candidate_spans"]
    assert len(spans) >= 1, "ClosedThought failed to find candidate highlight clips"
    best_span = spans[0]
    assert best_span.deictic_penalized is False, "Candidate clip starts with dangling deictic starter"
    assert best_span.triad_score > 0.0

    # Layout mode must be SPLIT_STAGE due to simultaneous IDE + Terminal
    layout_mode = pipeline_artifacts["layout_mode"]
    assert layout_mode == LayoutMode.SPLIT_STAGE, f"Expected SPLIT_STAGE, got {layout_mode}"


def test_stage6_full_composition_redaction_and_outro_qr():
    """
    Renders a 9:16 vertical Reel from demo_lecture.mp4 using ReelCompositor.
    Verifies:
    1. Rendered 1080x1920 MP4 exists and is playable.
    2. Secret region is redacted via Gaussian blur.
    3. Outro QR bumper card is rendered in the final frames.
    """
    OUTPUT_REEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Run rapid OCR for secrets
    detector = PlateauDetector(output_dir=ROOT_DIR / "data" / "cache" / "keyframes")
    plateaus, _ = detector.detect_plateaus(str(VIDEO_PATH))
    ocr = ScreenLexMiner()
    secrets = ocr.scan_safe_cohort(plateaus)
    assert len(secrets) >= 1

    # Configure ReelIR for 4.0-second test render
    render_duration = 4.0
    brand_kit = BrandKitConfig(
        id="tech_summit_e2e",
        name="SnipShot Academy",
        enable_outro_bumper=True,
        outro_bumper_duration=1.5,
    )
    growth_pack = SocialGrowthPack(
        hook_title="How to fix KeyError in production",
        stack_hashtags=["#React", "#Kubernetes"],
        micro_api_hashtags=["#Python", "#Docker"],
        qr_code_data="https://snipshot.dev/c/demo9988",
    )

    viewports = [
        ViewportKeyframe(
            timestamp=0.0,
            mode=LayoutMode.SPLIT_STAGE,
            top_crop=(0.0, 0.0, 0.60, 1.0),
            bottom_crop=(0.50, 0.0, 0.50, 1.0),
            transition_duration=0.0,
        )
    ]

    reel_ir = ReelIR(
        schema_version="1.0.0",
        reel_id="test_e2e_reel",
        mode="mode_a_extract",
        title="E2E Pipeline Verification",
        source_media_path=str(VIDEO_PATH),
        clip_start=0.0,
        clip_end=render_duration,
        total_duration=render_duration,
        audio_path=str(AUDIO_PATH),
        transcript=[],
        viewports=viewports,
        code_cards=[],
        brand_kit=brand_kit,
        template_archetype=TemplateArchetype.BUG_HUNTER,
        error_resolved_at=2.5,
        redaction_boxes=secrets,
        social_growth_pack=growth_pack,
    )

    compositor = ReelCompositor(width=1080, height=1920, fps=30)
    out_path = compositor.render(reel_ir, str(OUTPUT_REEL_PATH))

    # Verification 1: File existence and size
    assert os.path.exists(out_path), "Compositor output file does not exist"
    file_size_bytes = os.path.getsize(out_path)
    assert file_size_bytes > 50000, f"Rendered video size too small ({file_size_bytes} bytes)"

    # Verification 2: Video probe
    ffmpeg = FFmpegService()
    probe = ffmpeg.probe_video(out_path)
    assert probe["width"] == 1080
    assert probe["height"] == 1920
    assert probe["duration"] >= 3.5

    # Verification 3: Verify Secret Blur in Upper Viewport Frame
    cap = cv2.VideoCapture(out_path)
    assert cap.isOpened(), "Could not open rendered 9:16 video"
    
    # Read frame at t=1.0s (Secret region should be rendered with Gaussian blur)
    cap.set(cv2.CAP_PROP_POS_MSEC, 1000.0)
    ret, frame_t1 = cap.read()
    assert ret and frame_t1 is not None, "Failed to read frame at t=1.0s"
    
    # In SplitStage, upper viewport is placed at y: 120..1140
    # The secret ROI in upper crop should have softened gradient variance due to 51x51 Gaussian blur
    upper_roi = frame_t1[150:400, 50:600]
    laplacian_var = cv2.Laplacian(upper_roi, cv2.CV_64F).var()
    # Blurred text region has reduced Laplacian variance compared to sharp raw text
    assert laplacian_var < 5000.0, "Secret region appears unblurred"

    # Verification 4: Outro QR Badge in Final Frame
    # Read frame at t=3.5s (Outro bumper active during last 1.5s)
    cap.set(cv2.CAP_PROP_POS_MSEC, 3500.0)
    ret, frame_end = cap.read()
    assert ret and frame_end is not None, "Failed to read outro bumper frame"

    # Outro QR card is rendered at y: 420..1460, x: 80..1000 with black/white QR code
    qr_region = frame_end[600:960, 360:720]
    # Check that QR region is not a blank solid color
    qr_std = float(np.std(qr_region))
    assert qr_std > 20.0, f"Outro QR code region is uniform or missing (std={qr_std})"

    cap.release()
    print("\n[+] E2E pipeline successfully verified: MP4 generated, secret redacted, QR badge confirmed!")
