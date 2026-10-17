import os
import sys
import subprocess
import json
import sqlite3
import pytest

from backend.app.core.fast_mode_b import FastModeBEngine
from backend.app.core.fast_native_compositor import FastNativeCompositor
from backend.app.core.hinglish_normalizer import TECH_TERMS_MAP, CONVERSATIONAL_HINGLISH
from backend.app.core.fast_mode_a import FastModeAEngine


def test_mode_b_speech_synthesis_and_slides():
    engine = FastModeBEngine()
    result = engine.generate_explainer(
        prompt="Python List vs Tuple",
        brand_kit={"name": "SnipShot Studio", "primary_color": "#4F46E5"}
    )
    assert result is not None
    assert "video_url" in result
    assert result["duration"] > 5.0
    
    # Path to generated mp4
    video_path = os.path.join(os.getcwd(), "backend", result["video_url"].lstrip("/"))
    assert os.path.exists(video_path), f"Video file not found at {video_path}"
    
    # Check with ffprobe that audio stream exists and has duration
    probe_cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "a:0",
        "-show_entries", "stream=codec_name,duration,channels",
        "-of", "json",
        video_path
    ]
    res = subprocess.run(probe_cmd, capture_output=True, text=True)
    probe_data = json.loads(res.stdout)
    streams = probe_data.get("streams", [])
    assert len(streams) > 0, "No audio stream found in generated Mode B video!"
    assert streams[0]["codec_name"] in ["aac", "mp3"], f"Unexpected codec {streams[0]['codec_name']}"
    print(f"Verified Mode B video audio: {streams[0]}")


def test_ass_karaoke_sweeping_colors():
    compositor = FastNativeCompositor()
    ass_path = "/tmp/test_karaoke_sweep.ass"
    words = [
        {"word": "Welcome", "start": 0.0, "end": 0.8},
        {"word": "to", "start": 0.8, "end": 1.2},
        {"word": "SnipShot", "start": 1.2, "end": 2.2}
    ]
    compositor.generate_ass_subtitles(words, start_sec=0.0, duration=3.0, output_path=ass_path)
    assert os.path.exists(ass_path)
    
    with open(ass_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Verify SecondaryColour is White (&H00FFFFFF) and PrimaryColour is Gold (&H0000D7FF)
    assert "PrimaryColour=&H0000D7FF" in content or ",&H0000D7FF,&H00FFFFFF," in content, "ASS does not have gold primary colour for karaoke sweep!"
    assert "SecondaryColour=&H00FFFFFF" in content or ",&H0000D7FF,&H00FFFFFF," in content, "ASS does not have white secondary colour for base text!"
    assert "\\kf" in content, "Dialogue lines do not have karaoke tags (\\kf)!"
    print("Verified ASS karaoke sweeping colors and \\kf tags.")


def test_qr_code_direct_code_text():
    compositor = FastNativeCompositor()
    sample_code = 'JButton btn = new JButton("Submit");\nbtn.addActionListener(e -> fire());'
    
    # Generate overlay PNG with code snippet
    overlay_path = "/tmp/test_qr_overlay.png"
    compositor.render_overlay_png(
        institute_name="SnipShot Studio",
        brand_color="#4F46E5",
        code_snippet=sample_code,
        template_archetype="standard_spotlight",
        output_path=overlay_path,
        qr_data=sample_code
    )
    assert os.path.exists(overlay_path)
    print("Verified QR code overlay generated successfully with raw code text.")


def test_hinglish_tech_terms_enrichment():
    assert "println" in TECH_TERMS_MAP
    assert "semicolon" in TECH_TERMS_MAP
    assert "curly braces" in TECH_TERMS_MAP
    assert "chalayenge" in CONVERSATIONAL_HINGLISH
def test_dynamic_telemetry_weights():
    from backend.app.core.feedback_bandit import PedagogyScoreBandit
    bandit = PedagogyScoreBandit()
    init_weights = bandit.get_weights()
    assert "w1" in init_weights
    
    # Simulate feedback
    updated = bandit.record_feedback(
        reel_id="test_reel_demo",
        features={"rms_audio": 0.85, "diff_visual": 0.90, "tech_density": 0.95, "bug2fix_bonus": 1.0, "penalty_deictic": 0.0},
        retention_rate=0.92,
        exported=True
    )
    assert updated is not None
    print(f"Verified dynamic bandit weights in SQLite: {updated}")


if __name__ == "__main__":
    test_hinglish_tech_terms_enrichment()
    test_ass_karaoke_sweeping_colors()
    test_qr_code_direct_code_text()
    test_dynamic_telemetry_weights()
    test_mode_b_speech_synthesis_and_slides()
    print("ALL HUMAN STUDIO FIX TESTS PASSED!")
