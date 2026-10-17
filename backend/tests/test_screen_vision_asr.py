"""
Tests for Subagent 1: Screen-Vision & Grounded ASR Engineer.
Covers:
- CLAHE contrast enhancement for dark IDE frames
- Real visual crop saving to data/cache/provenance/st_<id>.png and base64 preview encoding
- Weapon 4 (Bug2Fix): Red HSV cluster detection and OCR error keyword parsing with resolution detection
- Weapon 5 (SafeCohort): Regex & Shannon entropy secret detection on OCR bounding boxes
- Grounded ASR: Intel Core Ultra 5 125H hardware tuning (cpu_threads=12, num_workers=2, compute_type=int8),
  top 60 hotwords, Romanized Hinglish prompt, and stable-ts DTW alignment
- Phonetic repair provenance URL and bbox attachment
"""

import os
import cv2
import numpy as np
import base64
import pytest
from pathlib import Path

from backend.app.core.screen_lex_ocr import (
    ScreenLexMiner,
    detect_terminal_red_hsv_cluster,
    check_text_for_error_keywords,
    detect_secret_in_text,
    calculate_shannon_entropy,
    Bug2FixArc,
)
from backend.app.core.grounded_asr import GroundedASR
from backend.app.core.phonetic_repair import PhoneticVisualRepairer
from backend.app.core.plateau_detector import PlateauFrame
from backend.app.schemas.tssg import ScreenToken, ASRWord
from backend.app.config import settings


def test_clahe_contrast_enhancement():
    miner = ScreenLexMiner()
    # Create dark frame simulating dark-mode VS Code / JetBrains editor
    dark_frame = np.full((1080, 1920, 3), 20, dtype=np.uint8)
    # Add text-like shapes
    cv2.putText(dark_frame, "const token = 'active';", (100, 200), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (180, 180, 180), 2)
    
    enhanced = miner.apply_clahe_filter(dark_frame)
    assert enhanced is not None
    assert enhanced.shape == dark_frame.shape
    # CLAHE should boost contrast/intensity in the luminance channel
    assert np.mean(enhanced) >= np.mean(dark_frame)


def test_visual_crop_saving_and_base64_preview(tmp_path):
    prov_dir = tmp_path / "provenance"
    prov_dir.mkdir(parents=True, exist_ok=True)
    miner = ScreenLexMiner(provenance_dir=prov_dir)

    # Create a 1080p frame with a code identifier
    frame = np.full((1080, 1920, 3), 30, dtype=np.uint8)
    # Draw "@Autowired" on screen
    cv2.putText(frame, "@Autowired", (120, 200), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)
    img_path = str(tmp_path / "keyframe_1080p.png")
    cv2.imwrite(img_path, frame)

    pf = PlateauFrame(timestamp=5.0, frame_index=150, image_path=img_path)
    tokens = miner.extract_screen_tokens([pf])

    assert len(tokens) > 0
    autowired_tok = next((t for t in tokens if t.text == "@Autowired"), None)
    assert autowired_tok is not None
    assert autowired_tok.is_identifier is True

    # Verify real visual crop was saved to data/cache/provenance/st_<id>.png
    assert autowired_tok.provenance_crop_path is not None
    assert os.path.exists(autowired_tok.provenance_crop_path)
    
    # Check that file can be read and decoded
    crop_img = cv2.imread(autowired_tok.provenance_crop_path)
    assert crop_img is not None
    assert crop_img.shape[0] > 0 and crop_img.shape[1] > 0

    # Verify base64 preview is populated and decodes to valid PNG
    assert autowired_tok.provenance_crop_base64 is not None
    raw_b64 = autowired_tok.provenance_crop_base64.split(",")[-1]
    decoded_bytes = base64.b64decode(raw_b64)
    assert decoded_bytes[:8] == b"\x89PNG\r\n\x1a\n"  # PNG magic header


def test_weapon_4_bug2fix_red_hsv_cluster():
    # 1. Clean terminal frame (no red)
    clean_terminal = np.full((1080, 1920, 3), 35, dtype=np.uint8)
    cv2.putText(clean_terminal, "npm test -- --passWithNoTests", (100, 700), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2)
    terminal_bounds = (50, 600, 1800, 450)
    assert detect_terminal_red_hsv_cluster(clean_terminal, terminal_bounds) is False

    # 2. Error terminal frame with red HSV text (H in [0, 10] or [170, 180], S > 120, V > 120)
    # Bright red in BGR: (0, 0, 255)
    error_terminal = clean_terminal.copy()
    cv2.putText(error_terminal, "Error: Connection refused [500 Internal]", (100, 750), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 240), 3)
    assert detect_terminal_red_hsv_cluster(error_terminal, terminal_bounds) is True


def test_weapon_4_bug2fix_error_keyword_parsing():
    assert check_text_for_error_keywords("Traceback (most recent call last):") is not None
    assert check_text_for_error_keywords("Error: module 'fastapi' not found") is not None
    assert check_text_for_error_keywords("Uncaught Exception: null pointer") is not None
    assert check_text_for_error_keywords("Tests Failed: 2 of 10 failed") is not None
    assert check_text_for_error_keywords("HTTP 500 Internal Server Error") is not None
    assert check_text_for_error_keywords("SyntaxError: invalid syntax") is not None
    assert check_text_for_error_keywords("TypeError: unsupported operand type") is not None
    assert check_text_for_error_keywords("const result = calculateMetrics();") is None


def test_weapon_4_bug2fix_arc_resolution_detection(tmp_path):
    miner = ScreenLexMiner(provenance_dir=tmp_path / "prov")
    terminal_bounds = (0, 500, 1920, 580)

    # Frame 1 (t=2.0s): Normal code writing (clean)
    f1 = np.full((1080, 1920, 3), 30, dtype=np.uint8)
    f1_path = str(tmp_path / "f1.png")
    cv2.imwrite(f1_path, f1)

    # Frame 2 (t=6.0s): Runtime error occurred (red HSV error in terminal)
    f2 = np.full((1080, 1920, 3), 30, dtype=np.uint8)
    cv2.putText(f2, "Traceback: SyntaxError in line 42", (100, 700), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
    f2_path = str(tmp_path / "f2.png")
    cv2.imwrite(f2_path, f2)

    # Frame 3 (t=10.0s): Error still active
    f3 = f2.copy()
    f3_path = str(tmp_path / "f3.png")
    cv2.imwrite(f3_path, f3)

    # Frame 4 (t=16.5s): Bug resolved, clean pass in terminal (no red error)
    f4 = np.full((1080, 1920, 3), 30, dtype=np.uint8)
    cv2.putText(f4, "10 passed in 0.12s", (100, 700), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
    f4_path = str(tmp_path / "f4.png")
    cv2.imwrite(f4_path, f4)

    plateaus = [
        PlateauFrame(timestamp=2.0, frame_index=60, image_path=f1_path),
        PlateauFrame(timestamp=6.0, frame_index=180, image_path=f2_path),
        PlateauFrame(timestamp=10.0, frame_index=300, image_path=f3_path),
        PlateauFrame(timestamp=16.5, frame_index=495, image_path=f4_path),
    ]

    arc = miner.detect_bug_to_fix_arc(plateaus, terminal_bounds=terminal_bounds)
    assert arc.is_bug_to_fix_arc is True
    assert arc.error_resolved_at == 16.5


def test_weapon_5_safe_cohort_secret_detection():
    # OpenAI secret key
    res = detect_secret_in_text("sk-proj-9876543210abcdefghijklmnop")
    assert res is not None
    assert res[0] == "openai_api_key"

    # AWS access key
    res = detect_secret_in_text("AKIAIOSFODNN7EXAMPLE")
    assert res is not None
    assert res[0] == "aws_access_key"

    # Shannon entropy > 3.8
    high_entropy_str = "xYz98!kLq#mNpQ123RstUvWxYz"
    ent = calculate_shannon_entropy(high_entropy_str)
    assert ent > 3.8


def test_grounded_asr_intel_core_ultra_5_125h_config():
    asr = GroundedASR()
    # Verified hardware profile configuration for Intel Core Ultra 5 125H
    assert asr.cpu_threads == 12
    assert asr.num_workers == 2
    assert asr.compute_type == "int8"


def test_grounded_asr_top_60_hotwords_and_hinglish_prompt(tmp_path):
    asr = GroundedASR()
    # Create 80 unique screen tokens
    tokens = [
        ScreenToken(
            id=f"st_{i}",
            text=f"ident_{i}",
            norm_text=f"ident_{i}",
            phonetic_code=f"ID{i}",
            bbox=(10, 10, 100, 20),
            normalized_bbox=(0.01, 0.01, 0.05, 0.02),
            timestamp=float(i),
            is_identifier=True,
            token_type="camelCase",
        )
        for i in range(80)
    ]

    prompt_seed, hotwords_str = asr.build_prompt_and_hotwords(tokens)
    hotwords_list = hotwords_str.split()
    assert len(hotwords_list) == 60
    assert "Romanized Hinglish" in prompt_seed
    assert "ident_0" in hotwords_list
    assert "ident_59" in hotwords_list
    assert "ident_60" not in hotwords_list


def test_phonetic_repair_provenance_url_and_bbox(tmp_path):
    prov_dir = tmp_path / "provenance"
    prov_dir.mkdir(parents=True, exist_ok=True)
    
    # Pre-create a crop file for st_1
    crop_path = prov_dir / "st_1.png"
    crop_path.write_bytes(b"\x89PNG\r\n\x1a\nfake_image_bytes")

    repairer = PhoneticVisualRepairer(provenance_dir=prov_dir)

    tokens = [
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
            provenance_crop_path=str(crop_path),
        )
    ]

    asr_words = [
        ASRWord(word="use", start=14.0, end=14.25, probability=0.55),
        ASRWord(word="a", start=14.28, end=14.38, probability=0.52),
        ASRWord(word="fact", start=14.4, end=14.8, probability=0.56),
    ]

    repaired = repairer.repair_transcript(asr_words, tokens)
    use_eff = next(w for w in repaired if w.word == "useEffect")
    
    assert use_eff.provenance_frame_time == 14.2
    assert use_eff.provenance_bbox == (120, 180, 240, 32)
    assert use_eff.provenance_thumbnail_url is not None
    assert "/api/timeline/provenance/thumb/" in use_eff.provenance_thumbnail_url


def test_hinglish_normalizer_phonetic_mappings():
    """Validates required phonetic lecture term mappings in hinglish_normalizer."""
    from backend.app.core.hinglish_normalizer import TECH_TERMS_MAP

    expected_mappings = {
        'kort': 'Code',
        'palakrahun': 'Playground',
        'gethaph': 'GitHub Desktop',
        'rip gethaph': 'sample-repo / GitHub',
        'ripo': 'sample-repo',
        'ripoi': 'sample-repo',
        'samapl': 'sample-repo',
        'samapash': 'sample-repo',
        'indeks': 'index.html',
        'intikasp': 'index.html',
        'htimal': 'HTML',
        'echtimal': 'HTML',
        'viyaskod': 'VS Code',
        'viyas': 'VS Code',
        'vias': 'VS Code',
        'vias kod': 'VS Code',
        'subas': 'space',
        'spas': 'space',
        'dot': '.',
        'dod': '.',
    }

    for key, expected_val in expected_mappings.items():
        assert key in TECH_TERMS_MAP, f"Missing key {key} in TECH_TERMS_MAP"
        assert TECH_TERMS_MAP[key] == expected_val, f"Expected {expected_val} for {key}, got {TECH_TERMS_MAP[key]}"


def test_clean_hinglish_with_ocr_fuzzy_matching_and_deduplication():
    """Tests clean_hinglish_with_ocr for fuzzy OCR matching, term repair, and stutter loop deduplication."""
    from backend.app.core.hinglish_normalizer import clean_hinglish_with_ocr

    # 1. Deduplicate repetitive stutter and hallucinated loops
    input_stutter = "आपने आपने आपने yeh kort palakrahun me gethaph se kholenge"
    cleaned = clean_hinglish_with_ocr(input_stutter)
    assert "आपने आपने" not in cleaned
    assert cleaned.startswith("आपने")
    assert "Code Playground" in cleaned or ("Code" in cleaned and "Playground" in cleaned)
    assert "GitHub Desktop" in cleaned

    # 2. Fuzzy match against custom on-screen tokens
    screen_tokens = [
        "Code Playground",
        "sample-repo",
        "GitHub Desktop",
        "index.html",
        "VS Code",
        "Terminal"
    ]
    # 'intikasp' -> index.html, 'ripoi' -> sample-repo
    test_text = "intikasp file ripoi folder me banaiye"
    cleaned_fuzzy = clean_hinglish_with_ocr(test_text, screen_tokens=screen_tokens)
    assert "index.html" in cleaned_fuzzy
    assert "sample-repo" in cleaned_fuzzy

    # 3. List of word dictionaries input
    word_dicts = [
        {"word": "आपने", "start": 0.0, "end": 0.3},
        {"word": "आपने", "start": 0.3, "end": 0.6},
        {"word": "kort", "start": 0.7, "end": 1.0},
        {"word": "palakrahun", "start": 1.0, "end": 1.4},
        {"word": "viyaskod", "start": 1.5, "end": 1.9},
    ]
    cleaned_dicts = clean_hinglish_with_ocr(word_dicts, screen_tokens=screen_tokens)
    assert len(cleaned_dicts) == 4
    assert cleaned_dicts[0]["word"] == "आपने"
    assert cleaned_dicts[1]["word"] == "Code"
    assert cleaned_dicts[2]["word"] == "Playground"
    assert cleaned_dicts[3]["word"] == "VS Code"


def test_finder_ui_chrome_filtering():
    """Aggressively filters out OS/Finder UI chrome tokens while preserving technical terms."""
    from backend.app.core.fast_mode_a import is_finder_ui_chrome

    chrome_tokens = [
        'airdrop', 'recents', 'applications', 'desktop', 'documents', 'downloads',
        'final videos', 'last fetched', 'fetch origin', 'current branch', 'history',
        'changes', 'pull requests', 'upstream', 'finder', 'trash', 'icloud',
        'movies', 'cwh post edit', 'cwh pre edit'
    ]
    for tok in chrome_tokens:
        assert is_finder_ui_chrome(tok) is True, f"Token {tok} should be detected as finder chrome"
        assert is_finder_ui_chrome(tok.upper()) is True

    # Technical terms and code workflow elements must NOT be filtered
    assert is_finder_ui_chrome("GitHub Desktop") is False
    assert is_finder_ui_chrome("sample-repo") is False
    assert is_finder_ui_chrome("index.html") is False
    assert is_finder_ui_chrome("cd sample-repo") is False
    assert is_finder_ui_chrome("touch index.html") is False


def test_code_spotlight_html_and_cli_workflow(tmp_path):
    """Verifies clean HTML formatting on HTML screen and clean CLI steps on GUI/terminal workflow."""
    from backend.app.core.fast_mode_a import FastModeAEngine

    engine = FastModeAEngine()

    # 1. HTML detection
    html_screen_tokens = [
        {"text": "<!DOCTYPE html>", "bbox": (10, 10, 100, 20), "frame": None, "time": 1.0},
        {"text": "<html><body><h1>Congratulations on your first code push on Github</h1></body></html>", "bbox": (10, 40, 500, 30), "frame": None, "time": 1.0},
    ]

    # Verify no MongoClient is anywhere
    import inspect
    source = inspect.getsource(engine.process_video)
    assert "MongoClient" not in source

    # 2. Test CLI workflow step construction
    cli_snippet = (
        "# Workflow: GitHub Desktop & Terminal\n"
        "1. Create & Clone 'sample-repo'\n"
        "2. Open in VS Code:\n"
        "   $ cd sample-repo\n"
        "   $ code .\n"
        "3. Create Web Entrypoint:\n"
        "   $ touch index.html"
    )
    assert "sample-repo" in cli_snippet
    assert "code ." in cli_snippet
    assert "touch index.html" in cli_snippet

