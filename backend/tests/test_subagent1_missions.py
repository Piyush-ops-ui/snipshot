"""
Tests for Subagent 1 missions:
1. Fix vertical single-character code bug (A \\n 1 \\n a) and horizontal box grouping
2. Perceptual 64x36 Delta-Frame Slide-Skip Gate (check_slide_skip)
3. Two-Stage Clean Subtitle Pipeline (repair_transcript_contextual)
4. 4-Signal Multimodal Candidate Scorer (PedagogyScoreBandit weights)
5. Mode B fake boilerplate elimination & ML curricula validation
"""

import os
import json
import numpy as np
import pytest
from unittest.mock import patch, MagicMock

from backend.app.core.fast_mode_a import (
    check_slide_skip,
    auto_indent_code,
    repair_transcript_contextual,
    FastModeAEngine,
    OUTPUTS_DIR,
)
from backend.app.core.fast_mode_b import FastModeBEngine
from backend.app.core.feedback_bandit import PedagogyScoreBandit


# ============================================================================
# 1. Perceptual 64x36 Delta-Frame Slide-Skip Gate
# ============================================================================

def test_check_slide_skip_identical_and_static_frames():
    """Identical or near-identical frames should be detected as static (< 2.0% delta)."""
    # 1. Identical frames
    f1 = np.full((720, 1280, 3), 120, dtype=np.uint8)
    f2 = np.full((720, 1280, 3), 120, dtype=np.uint8)
    
    is_skip, delta = check_slide_skip(f2, f1, threshold_pct=2.0)
    assert is_skip is True
    assert delta == 0.0

    # 2. Sub-threshold variation (< 2.0%)
    f_slight = f1.copy()
    f_slight[0:10, 0:10] = 125  # Tiny change
    is_skip, delta = check_slide_skip(f_slight, f1, threshold_pct=2.0)
    assert is_skip is True
    assert delta < 2.0


def test_check_slide_skip_motion_and_content_change():
    """Significant visual changes (> 2.0% delta) must NOT be skipped."""
    f1 = np.zeros((720, 1280, 3), dtype=np.uint8)
    f2 = np.full((720, 1280, 3), 255, dtype=np.uint8)  # Complete white screen
    
    is_skip, delta = check_slide_skip(f2, f1, threshold_pct=2.0)
    assert is_skip is False
    assert delta >= 2.0
    assert delta > 90.0

    # First frame (prev=None) must never be skipped
    is_skip, delta = check_slide_skip(f1, None, threshold_pct=2.0)
    assert is_skip is False
    assert delta == 100.0


# ============================================================================
# 2. Vertical Single-Character Code Fix & Horizontal Grouping
# ============================================================================

def test_auto_indent_code_string_and_list_safety():
    """Ensures auto_indent_code never explodes strings into single characters separated by newlines."""
    # Direct string input
    code_str = 'age = int(input("enter age: "))\nif age >= 18:\n    print("can vote")'
    result = auto_indent_code(code_str)
    assert "a\ng\ne" not in result
    assert "age = int(input(" in result
    assert "print(\"can vote\")" in result

    # List of strings input
    lines = ['age = int(input("enter age: "))', 'if age >= 18:', 'print("can vote")']
    result_list = auto_indent_code(lines)
    assert "a\ng\ne" not in result_list
    assert "    print(\"can vote\")" in result_list


def test_extract_code_from_frames_horizontal_grouping_and_filtering():
    """Tests FastModeAEngine._extract_code_from_frames box grouping within 14px vertical tolerance and single-char rejection."""
    engine = FastModeAEngine()
    dummy_frame = np.zeros((720, 1280, 3), dtype=np.uint8)

    # Tokens simulating OCR boxes:
    # "age =", "int(input(", "\"enter age: \"))" on center_y ~ 100, within 14px
    # And noise items "A", "1", "a" are single chars
    clean_screen_tokens = [
        # Noise single characters: "A", "1", "a"
        {"text": "A", "bbox": [10, 100, 10, 15], "time": 1.0, "frame": dummy_frame},
        {"text": "1", "bbox": [10, 140, 10, 15], "time": 1.0, "frame": dummy_frame},
        {"text": "a", "bbox": [10, 180, 10, 15], "time": 1.0, "frame": dummy_frame},
        
        # Real code line split across 3 horizontal bounding boxes on y ~ 100
        {"text": "age =", "bbox": [50, 95, 70, 20], "time": 1.0, "frame": dummy_frame},
        {"text": "int(input(", "bbox": [130, 96, 85, 20], "time": 1.0, "frame": dummy_frame},
        {"text": "\"enter age: \"))", "bbox": [225, 94, 150, 20], "time": 1.0, "frame": dummy_frame},
        
        # Next line on y ~ 140
        {"text": "if age >= 18:", "bbox": [50, 138, 120, 20], "time": 1.0, "frame": dummy_frame},
        
        # Next indented line on y ~ 180
        {"text": "print(\"can vote\")", "bbox": [90, 178, 160, 20], "time": 1.0, "frame": dummy_frame},
        
        # Next line on y ~ 220
        {"text": "else:", "bbox": [50, 218, 60, 20], "time": 1.0, "frame": dummy_frame},
        
        # Next indented line on y ~ 260
        {"text": "print(\"cannot vote\")", "bbox": [90, 258, 180, 20], "time": 1.0, "frame": dummy_frame},
    ]

    code = engine._extract_code_from_frames(
        sampled_frames=[dummy_frame],
        clean_screen_tokens=clean_screen_tokens,
        sample_times=[1.0]
    )

    # Assertions:
    # 1. No single-character vertical sequence
    assert "A\n1\na" not in code
    lines = [line.strip() for line in code.split("\n")]
    assert "A" not in lines
    assert "1" not in lines
    assert "a" not in lines

    # 2. Horizontal boxes successfully merged
    assert 'age = int(input( "enter age: "))' in code or 'age = int(input(' in code
    assert "if age >= 18:" in code
    assert 'print("can vote")' in code
    assert "else:" in code
    assert 'print("cannot vote")' in code


# ============================================================================
# 3. Two-Stage Clean Subtitle Pipeline
# ============================================================================

def test_repair_transcript_contextual_ai_success():
    """Validates contextual AI subtitle cleaner using mock Pollinations API."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "clean_subtitles": "Now we implement the gradient descent optimization loop.",
                        "clean_code": "w -= lr * dw"
                    })
                }
            }
        ]
    }

    with patch("httpx.Client.post", return_value=mock_resp):
        cleaned, code = repair_transcript_contextual(
            raw_text="um so now we like implement gradient decent optimization loop ok",
            screen_tokens=["gradient", "descent", "optimization", "loop"]
        )

    assert cleaned == "Now we implement the gradient descent optimization loop."
    assert code == "w -= lr * dw"


def test_repair_transcript_contextual_fallback_on_timeout():
    """When Pollinations times out or fails, fallback cleanly applies token normalization without crashing."""
    with patch("httpx.Client.post", side_effect=Exception("Connection timeout")):
        cleaned, code = repair_transcript_contextual(
            raw_text="hum gradient decent loop chalayenge",
            screen_tokens=["gradient", "descent", "loop"]
        )

    assert "gradient descent loop" in cleaned


# ============================================================================
# 4. 4-Signal Multimodal Candidate Scorer
# ============================================================================

def test_score_multimodal_window_formula():
    """Validates the 4-signal multimodal candidate scoring formula with SQLite weights."""
    engine = FastModeAEngine()
    bandit = PedagogyScoreBandit()
    weights = bandit.get_weights()

    with patch("backend.app.core.fast_mode_a.probe_audio_energy", return_value=0.04):
        # 1. Clean technical candidate
        res_clean = engine._score_multimodal_window(
            video_path="dummy.mp4",
            start_sec=10.0,
            end_sec=45.0,
            tokens=["numpy", "linear", "regression", "weights", "=", "y_pred"],
            weights=weights,
            cap=None,
        )

        assert 0.0 <= res_clean["score"] <= 100.0
        assert "vocal_score" in res_clean
        assert "visual_diff_score" in res_clean
        assert "tech_density_score" in res_clean
        assert "closure_score" in res_clean
        assert "deictic_penalty" in res_clean
        assert res_clean["deictic_penalty"] == 0.0
        assert "why_selected" in res_clean
        assert len(res_clean["why_selected"]) > 0

        # 2. Candidate with deictic starter
        res_deictic = engine._score_multimodal_window(
            video_path="dummy.mp4",
            start_sec=10.0,
            end_sec=45.0,
            tokens=["isko", "dekho", "code", "run", "karo"],
            weights=weights,
            cap=None,
        )
        assert res_deictic["deictic_penalty"] == 1.0
        assert res_deictic["score"] < res_clean["score"]


# ============================================================================
# 5. Mode B Fake Boilerplate Elimination & ML Curricula
# ============================================================================

def test_mode_b_ml_curricula_gradient_descent():
    """Mode B contains genuine Gradient Descent curriculum without boilerplate."""
    engine = FastModeBEngine()
    scenes = engine._compile_script("Gradient Descent in Linear Regression")

    assert len(scenes) >= 3
    all_code = " ".join(s.get("code", "") for s in scenes)
    assert "dw =" in all_code or "y_pred" in all_code or "w -=" in all_code

    all_text = json.dumps(scenes)
    assert "Mastering Gradient Descent in in 45 seconds" not in all_text
    assert "Mastering " not in all_text
    assert "console.log('Mastering" not in all_text
    assert "execute_concept" not in all_text


def test_mode_b_ml_curricula_neural_networks():
    """Mode B contains genuine Neural Networks curriculum."""
    engine = FastModeBEngine()
    scenes = engine._compile_script("Neural Networks")

    all_code = " ".join(s.get("code", "") for s in scenes)
    assert "relu" in all_code or "forward" in all_code or "softmax" in all_code
    assert "execute_concept" not in all_code


def test_mode_b_ml_curricula_kmeans():
    """Mode B contains genuine K-Means Clustering curriculum."""
    engine = FastModeBEngine()
    scenes = engine._compile_script("K-Means Clustering")

    all_code = " ".join(s.get("code", "") for s in scenes)
    assert "centroids" in all_code or "cluster" in all_code
    assert "execute_concept" not in all_code


def test_mode_b_generate_explainer_execution():
    """Verifies end-to-end generate_explainer produces real assets without crashing."""
    engine = FastModeBEngine()
    result = engine.generate_explainer("Gradient Descent in Linear Regression")

    assert result["status"] == "success"
    assert "reel_id" in result
    assert "scenes" in result
    assert len(result["scenes"]) >= 3
    assert "video_url" in result
    out_file = OUTPUTS_DIR / f"{result['reel_id']}.mp4"
    assert out_file.exists()
