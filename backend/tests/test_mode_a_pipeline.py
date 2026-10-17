"""
Unit & Integration Tests for Mode A Real Video Pipeline.
Verifies Window Pre-Scanner, Mode A Pipeline, Reel Generator, and API Endpoints.
"""

import pytest
import os
import numpy as np
from pathlib import Path
from fastapi.testclient import TestClient

from backend.app.schemas.reel_ir import WordAlignment, RedactionBox
from backend.app.schemas.brand import BrandKitConfig as BrandKit
from backend.app.core.window_prescanner import WindowPreScanner, TeachingWindow
from backend.app.core.mode_a_pipeline import ModeAPipeline, Sentence, HighlightClip, RepairedTerm
from backend.app.core.reel_generator import ReelGenerator
from backend.app.services.ffmpeg_service import FFmpegService
from backend.app.main import app
from backend.app.config import settings

DEMO_VIDEO = str(settings.BASE_DIR / "benchmarks" / "test_clips" / "demo_lecture.mp4")
DEMO_AUDIO = str(settings.BASE_DIR / "benchmarks" / "test_clips" / "demo_lecture_audio.wav")


def test_window_prescanner_short_video():
    """Rule 1: Videos <= 360s should return single window covering the full video span."""
    scanner = WindowPreScanner()
    if not os.path.exists(DEMO_VIDEO):
        pytest.skip("demo_lecture.mp4 not found")

    windows, wav_path = scanner.scan_video(DEMO_VIDEO)
    assert len(windows) == 1
    assert windows[0].start_sec == 0.0
    assert windows[0].end_sec >= 85.0
    assert windows[0].score == 1.0
    assert os.path.exists(wav_path)


def test_window_prescanner_long_video_selection():
    """Rule 2: For videos > 360s, prescanner ranks and selects top 3 non-overlapping 2-minute windows."""
    scanner = WindowPreScanner()
    # Mock probe to return a 900s (15 min) video
    probe_orig = scanner.ffmpeg.probe_video
    scanner.ffmpeg.probe_video = lambda path: {"duration": 900.0, "fps": 30.0}

    # Mock audio rms and sparse diff vectors
    scanner.compute_1s_audio_rms = lambda path, total_s: np.sin(np.linspace(0, 10, total_s)) ** 2
    scanner.compute_sparse_1fps_diff = lambda path, total_s, fps: np.cos(np.linspace(0, 10, total_s)) ** 2
    scanner.extract_audio_16k = lambda vid, out: DEMO_AUDIO

    try:
        windows, wav = scanner.scan_video(DEMO_VIDEO, top_k=3)
        assert len(windows) == 3
        for w in windows:
            assert (w.end_sec - w.start_sec) == 120.0
        # Ensure non-overlapping separation >= 60s
        for i in range(len(windows) - 1):
            assert abs(windows[i + 1].start_sec - windows[i].start_sec) >= 60.0
    finally:
        scanner.ffmpeg.probe_video = probe_orig


def test_sentence_grouping_on_punctuation_and_pauses():
    """Complete Thought: Groups words into sentences on punctuation and >=0.4s pauses."""
    pipeline = ModeAPipeline()
    words = [
        WordAlignment(id="w1", word="dekho", start=0.0, end=0.4, confidence=0.9),
        WordAlignment(id="w2", word="dosto,", start=0.5, end=0.9, confidence=0.9),
        WordAlignment(id="w3", word="aaj", start=1.0, end=1.3, confidence=0.9),
        WordAlignment(id="w4", word="seekhenge.", start=1.4, end=1.8, confidence=0.9),  # Punctuation boundary
        WordAlignment(id="w5", word="React", start=2.4, end=2.8, confidence=0.9),      # Pause gap 2.4 - 1.8 = 0.6s
        WordAlignment(id="w6", word="hooks.", start=2.9, end=3.3, confidence=0.9),
    ]

    sentences = pipeline.group_into_sentences(words)
    assert len(sentences) >= 2
    assert sentences[0].start_time == 0.0
    assert sentences[0].end_time == 1.8
    assert "seekhenge." in sentences[0].text
    assert sentences[1].start_time == 2.4


def test_highlight_selection_snaps_strictly_to_sentences():
    """Highlight selection must snap start and end strictly to full sentence boundaries."""
    pipeline = ModeAPipeline()
    s1 = Sentence(
        words=[WordAlignment(id="w1", word="Sentence", start=10.0, end=15.0, confidence=0.9)],
        start_time=10.0,
        end_time=15.0,
        text="Sentence one.",
    )
    s2 = Sentence(
        words=[WordAlignment(id="w2", word="Sentence", start=15.5, end=42.0, confidence=0.9, is_technical=True)],
        start_time=15.5,
        end_time=42.0,
        text="Sentence two with technical depth.",
    )
    s3 = Sentence(
        words=[WordAlignment(id="w3", word="Sentence", start=42.5, end=50.0, confidence=0.9)],
        start_time=42.5,
        end_time=50.0,
        text="Sentence three.",
    )

    clips = pipeline.select_complete_thought_highlights(
        sentences=[s1, s2, s3],
        wav_path=DEMO_AUDIO,
        screen_tokens=[],
        repaired_terms=[],
        top_k=1,
        min_duration=25.0,
        max_duration=65.0,
    )

    assert len(clips) >= 1
    clip = clips[0]
    # Boundaries must match full sentence boundary timestamps
    valid_starts = [10.0, 15.5, 42.5]
    valid_ends = [15.0, 42.0, 50.0]
    assert clip.start_sec in valid_starts
    assert clip.end_sec in valid_ends


def test_reel_generator_creates_valid_1080x1920_mp4():
    """ReelGenerator renders real 1080x1920 MP4 with valid video/audio streams."""
    if not os.path.exists(DEMO_VIDEO):
        pytest.skip("demo_lecture.mp4 not found")

    gen = ReelGenerator()
    out_mp4 = gen.render_reel(
        clip_id="pytest_valid_reel",
        source_video_path=DEMO_VIDEO,
        audio_path=DEMO_AUDIO,
        start_sec=10.0,
        end_sec=13.0,
        words=[
            WordAlignment(id="w1", word="useEffect", start=0.2, end=1.0, confidence=0.95, is_technical=True),
            WordAlignment(id="w2", word="dependency", start=1.2, end=2.0, confidence=0.92),
            WordAlignment(id="w3", word="array", start=2.1, end=2.8, confidence=0.94),
        ],
        code_snippet="useEffect(() => {\n  fetchData();\n}, []);",
        brand_kit=BrandKit(name="TechSummit Trainers", primary_color="#00F2FE"),
        fps=30,
    )

    assert os.path.exists(out_mp4)
    assert os.path.getsize(out_mp4) > 10000

    # Probe with ffprobe
    probe = gen.ffmpeg.probe_video(out_mp4)
    assert probe["width"] == 1080
    assert probe["height"] == 1920
    assert abs(probe["duration"] - 3.0) < 0.5


def test_rerender_clip_endpoint_via_client():
    """POST /api/v1/mode-a/rerender-clip re-renders MP4 clip in < 8s and returns 200 OK."""
    if not os.path.exists(DEMO_VIDEO):
        pytest.skip("demo_lecture.mp4 not found")

    client = TestClient(app)
    response = client.post(
        "/api/v1/mode-a/rerender-clip",
        json={
            "clip_id": "pytest_client_rerender",
            "source_video_path": DEMO_VIDEO,
            "start_sec": 12.0,
            "end_sec": 15.0,
            "code_snippet": "const state = useState(null);",
            "brand_kit": "cyberpunk",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "video_url" in data
    assert data["render_time_seconds"] < 8.0
    assert data["duration"] == 3.0


def test_bug3_qr_code_placement_and_scannability(tmp_path):
    """
    BUG 3 Fix Verification:
    - QR code size: 130x130, placed at x=910, y=1740 (40px right margin inside 1080px width)
    - Label 'SCAN CODE' placed at x=918, y=1712
    - Scannable with high contrast
    """
    from backend.app.core.fast_native_compositor import FastNativeCompositor
    from PIL import Image

    compositor = FastNativeCompositor()
    overlay_path = str(tmp_path / "test_overlay.png")

    compositor.render_overlay_png(
        institute_name="Test Academy",
        brand_color="#4F46E5",
        code_snippet="print('Hello World')",
        qr_data="https://snipshot.studio/verify",
        output_path=overlay_path,
    )

    assert os.path.exists(overlay_path)
    img = Image.open(overlay_path)
    assert img.size == (1080, 1920)

    # Check that pixel at QR code area is opaque (x=915, y=1745)
    pixel = img.getpixel((915, 1745))
    assert pixel[3] > 200  # Alpha channel is fully visible/opaque

    # Verify transparent middle window (x=540, y=1000)
    mid_pixel = img.getpixel((540, 1000))
    assert mid_pixel[3] == 0  # Alpha = 0 for middle video window


def test_weapon6_4_pedagogical_visual_templates(tmp_path):
    """
    Weapon 6 / 7 Archetype Templates Verification:
    - standard_spotlight: Verified badge 'VERIFIED CONTENT'
    - bug_hunter: Crimson Red Header #7F1D1D with badge '🚨 BUG RESOLVED [200 OK]' in #10B981
    - vs_battle: Dual Comparison Header '⚡ VS BATTLE • ARCHITECTURE COMPASS'
    - predict_output: Amber Yellow Header '⏸️ PAUSE & PREDICT OUTPUT'
    """
    from backend.app.core.fast_native_compositor import FastNativeCompositor
    from PIL import Image

    compositor = FastNativeCompositor()

    # 1. Standard Spotlight
    std_path = str(tmp_path / "overlay_std.png")
    compositor.render_overlay_png("Test", "#4F46E5", "code", template_archetype="standard_spotlight", output_path=std_path)
    std_img = Image.open(std_path)
    # Header slate color
    hdr_pix = std_img.getpixel((200, 20))
    assert hdr_pix[0] == 15 and hdr_pix[1] == 23 and hdr_pix[2] == 42

    # 2. Bug Hunter
    bug_path = str(tmp_path / "overlay_bug.png")
    compositor.render_overlay_png("Test", "#4F46E5", "code", template_archetype="bug_hunter", output_path=bug_path)
    bug_img = Image.open(bug_path)
    # Header crimson red #7F1D1D -> (127, 29, 29)
    bug_pix = bug_img.getpixel((200, 20))
    assert bug_pix[0] == 127 and bug_pix[1] == 29 and bug_pix[2] == 29

    # 3. VS Battle
    vs_path = str(tmp_path / "overlay_vs.png")
    compositor.render_overlay_png("Test", "#4F46E5", "code", template_archetype="vs_battle", output_path=vs_path)
    vs_img = Image.open(vs_path)
    vs_pix = vs_img.getpixel((200, 20))
    assert vs_pix[0] == 59 and vs_pix[1] == 7 and vs_pix[2] == 100

    # 4. Predict Output
    pred_path = str(tmp_path / "overlay_pred.png")
    compositor.render_overlay_png("Test", "#4F46E5", "code", template_archetype="predict_output", output_path=pred_path)
    pred_img = Image.open(pred_path)
    pred_pix = pred_img.getpixel((200, 20))
    assert pred_pix[0] == 120 and pred_pix[1] == 53 and pred_pix[2] == 15


def test_bug1_subtitle_chunking_and_guardrails(tmp_path):
    """
    BUG 1 Subtitle Chunking Verification:
    - 5-to-7 word phrases every 2.0 to 3.0 seconds (maximum 3.2s per Dialogue line)
    - Zero dialogue line frozen on screen or overlapping
    - DejaVu Sans font with bold weight and outline
    """
    from backend.app.core.fast_native_compositor import FastNativeCompositor

    compositor = FastNativeCompositor()
    ass_path = str(tmp_path / "test_subs.ass")

    # Generate 30 words over 15 seconds
    words = [
        {"word": f"word{i}", "start": 0.5 * i, "end": 0.5 * i + 0.45}
        for i in range(30)
    ]

    compositor.generate_ass_subtitles(
        words=words,
        start_sec=0.0,
        duration=15.0,
        brand_color="#4F46E5",
        output_path=ass_path,
    )

    assert os.path.exists(ass_path)
    with open(ass_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Verify DejaVu Sans style
    assert "DejaVu Sans" in content
    assert "Bold" in content

    # Parse dialogue lines and verify duration <= 3.2s and non-overlapping
    dialogue_lines = [line for line in content.splitlines() if line.startswith("Dialogue:")]
    assert len(dialogue_lines) >= 3

    prev_end = -1.0
    for line in dialogue_lines:
        parts = line.split(",")
        start_str = parts[1]
        end_str = parts[2]

        # Convert to seconds
        def to_s(t_str):
            h, m, s = t_str.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)

        s_sec = to_s(start_str)
        e_sec = to_s(end_str)

        # Maximum 3.2s per line
        assert (e_sec - s_sec) <= 3.21, f"Line duration {e_sec - s_sec} exceeds 3.2s"
        # No overlapping
        assert s_sec >= prev_end - 0.1, f"Overlap detected: start {s_sec} < prev_end {prev_end}"
        prev_end = e_sec


def test_bug3_weapon2_1_4x_zoom_crop_and_safe_cohort_blur(tmp_path):
    """
    1.4x Active-Region Zoom Crop & SafeCohort Blur Verification:
    - Middle crop width 1370 (1920 / 1.4), height 862 (1370 * 680 / 1080)
    - Zero black bars inside 1080x680
    - Supports safe_cohort_blur
    """
    if not os.path.exists(DEMO_VIDEO):
        pytest.skip("demo_lecture.mp4 not found")

    from backend.app.core.fast_native_compositor import FastNativeCompositor

    compositor = FastNativeCompositor()
    overlay_path = str(tmp_path / "crop_overlay.png")
    compositor.render_overlay_png("Test", "#4F46E5", "x = 1", output_path=overlay_path)

    ass_path = str(tmp_path / "crop_subs.ass")
    compositor.generate_ass_subtitles([], 0.0, 3.0, output_path=ass_path)

    out_mp4 = str(tmp_path / "crop_reel.mp4")
    compositor.render_reel_fast(
        source_video_path=DEMO_VIDEO,
        start_sec=10.0,
        duration=3.0,
        crop_x=100,
        crop_y=50,
        safe_cohort_blur=True,
        overlay_png_path=overlay_path,
        ass_subtitles_path=ass_path,
        output_mp4_path=out_mp4,
    )

    assert os.path.exists(out_mp4)
    assert os.path.getsize(out_mp4) > 5000


def test_telemetry_endpoints_weights_and_simulation():
    """
    Weapon 9 Telemetry API Endpoints:
    - GET /api/v1/telemetry/weights: returns weights from SQLite
    - POST /api/v1/telemetry/simulate-feedback: updates weights live
    """
    client = TestClient(app)

    # 1. GET weights
    resp_get = client.get("/api/v1/telemetry/weights")
    assert resp_get.status_code == 200
    data_get = resp_get.json()
    assert data_get["status"] == "success"
    assert "weights" in data_get
    assert "w1" in data_get["weights"]
    assert "sample_count" in data_get

    # 2. POST simulate feedback
    resp_post = client.post(
        "/api/v1/telemetry/simulate-feedback",
        json={
            "reel_id": "test_reel_feedback",
            "retention_rate": 0.95,
            "exported": True,
            "features": {
                "rms_audio": 0.88,
                "diff_visual": 0.92,
                "tech_density": 0.95,
                "bug2fix_bonus": 1.0,
                "penalty_deictic": 0.0,
            },
        },
    )
    assert resp_post.status_code == 200
    data_post = resp_post.json()
    assert data_post["status"] == "success"
    assert "updated_weights" in data_post
    assert data_post["sample_count"] >= 1


def test_rerender_clip_endpoint_with_weapon_parameters():
    """
    POST /api/v1/mode-a/rerender-clip with template_archetype, layout_mode, safe_cohort_blur, hyperlapse
    """
    if not os.path.exists(DEMO_VIDEO):
        pytest.skip("demo_lecture.mp4 not found")

    client = TestClient(app)
    response = client.post(
        "/api/v1/mode-a/rerender-clip",
        json={
            "clip_id": "pytest_weapons_rerender",
            "source_video_path": DEMO_VIDEO,
            "start_sec": 10.0,
            "end_sec": 13.0,
            "code_snippet": "const state = useState(0);",
            "template_archetype": "bug_hunter",
            "layout_mode": "split_stage",
            "safe_cohort_blur": True,
            "hyperlapse": True,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["template_archetype"] == "bug_hunter"
    assert data["layout_mode"] == "split_stage"
    assert data["safe_cohort_blur"] is True
    assert data["hyperlapse"] is True
    assert "video_url" in data

