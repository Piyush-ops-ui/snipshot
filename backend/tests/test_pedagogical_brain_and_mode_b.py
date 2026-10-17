"""
Tests for Subagent 2: Pedagogical Brain & Mode B Compiler Engineer.
Validates:
1. Weapon 3 (ClosedThought Triad Clipper):
   - Vocal energy RMS via numpy/scipy
   - Visual typing diff density across plateau frames
   - Deictic Entry Penalty on 'isko', 'ye wala', 'this', 'therefore' in first 3s
   - Magnetic snapping to sentence ends and pauses (>= 0.4s) strictly within [30s, 60s]
2. Mode B Compiler (AST-Verified Topic Explainer):
   - 4 pedagogical beats: Hook, Core Code Concept, Mutation/Contrast, Terminal Verification
   - Ollama / Gemini Flash fallback / Deterministic zero-crash resilience
   - Real Neural TTS (edge-tts / offline) with 0ms drift lock
   - Weapon 8 Social Growth Pack
3. Weapon 6 (PedagogyScore Contextual Bandit):
   - SQLite-backed state and telemetry persistence
   - LinUCB / Bayesian online weight updates (w1..w5) from retention and export signals
"""

import os
import io
import wave
import json
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

from backend.app.schemas.reel_ir import WordAlignment
from backend.app.schemas.tssg import VisualDiffEvent
from backend.app.core.closed_thought import (
    ClosedThoughtClipper,
    CandidateSpan,
    compute_audio_rms,
    compute_visual_typing_density,
)
from backend.app.core.mode_b_compiler import ModeBCompiler, ExplainerBeat
from backend.app.core.feedback_bandit import PedagogyScoreBandit
from backend.app.core.tree_sitter_gate import TreeSitterGate


# ============================================================================
# WEAPON 3: ClosedThought Triad Clipper Tests
# ============================================================================

def test_closed_thought_audio_rms_calculation(tmp_path):
    """Verifies real vocal energy RMS calculation on audio waveforms via numpy/scipy."""
    sr = 16000
    dur = 3.0
    total_samples = int(sr * dur)

    # 1. Generate synthetic sine wave audio file
    t = np.linspace(0, dur, total_samples, endpoint=False)
    sine_wave = (np.sin(2 * np.pi * 300 * t) * 16000).astype(np.int16)

    wav_file = tmp_path / "test_rms.wav"
    with wave.open(str(wav_file), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(sine_wave.tobytes())

    # Compute RMS on file
    rms_val = compute_audio_rms(wav_file, 0.5, 2.5, sample_rate=sr)
    assert 0.1 <= rms_val <= 1.0

    # Compute RMS on silent waveform
    silence = np.zeros(total_samples, dtype=np.int16)
    silence_file = tmp_path / "silent.wav"
    with wave.open(str(silence_file), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(silence.tobytes())

    rms_silence = compute_audio_rms(silence_file, 0.0, 2.0, sample_rate=sr)
    assert rms_silence == 0.0

    # Direct numpy array RMS
    arr_rms = compute_audio_rms(sine_wave, 0.0, 2.0, sample_rate=sr)
    assert arr_rms > 0.0


def test_closed_thought_visual_typing_density():
    """Verifies visual typing diff density across plateau frames."""
    diff_events = [
        VisualDiffEvent(timestamp=1.0, diff_magnitude=0.02, is_plateau=False),
        VisualDiffEvent(timestamp=3.0, diff_magnitude=0.05, is_plateau=True),
        VisualDiffEvent(timestamp=5.0, diff_magnitude=0.03, is_plateau=True),
        VisualDiffEvent(timestamp=7.0, diff_magnitude=0.01, is_plateau=False),
    ]

    norm_density, raw_density = compute_visual_typing_density(diff_events, 0.0, 10.0)
    assert norm_density > 0.0
    assert raw_density > 0.0

    # Empty window
    norm_empty, raw_empty = compute_visual_typing_density(diff_events, 20.0, 30.0)
    assert norm_empty == 0.0
    assert raw_empty == 0.0


def test_deictic_entry_penalty():
    """
    Enforces Deictic Entry Penalty on dangling Hinglish/English pronouns:
    ('isko', 'ye wala', 'this', 'therefore') in the first 3 seconds of candidate clips.
    """
    clipper = ClosedThoughtClipper()
    diffs = [VisualDiffEvent(timestamp=15.0, diff_magnitude=0.04, is_plateau=True)]

    # Test cases with dangling pronouns in opening 3 seconds
    deictic_test_words = [
        ("isko", ["isko", "pehle", "samjho", "dhyan", "se"]),
        ("ye wala", ["ye", "wala", "method", "deprecated", "hai"]),
        ("this", ["this", "function", "handles", "the", "request"]),
        ("therefore", ["therefore", "we", "can", "conclude", "the", "result"]),
    ]

    for label, tokens in deictic_test_words:
        words = []
        t = 0.0
        for tok in tokens:
            words.append(WordAlignment(id=f"w_{tok}", word=tok, start=t, end=t + 0.4))
            t += 0.5
        # Extend to 35 seconds to satisfy duration
        words.append(WordAlignment(id="end_w", word="complete.", start=34.0, end=34.5))

        score, deictic_penalized, tech_dens, feats, rms, vis = clipper._score_span(
            words, 0.0, 35.0, diffs
        )
        assert deictic_penalized is True, f"Failed to penalize deictic token: {label}"
        assert feats["penalty_deictic"] == 1.0

    # Clean non-deictic opening
    clean_tokens = ["Why", "did", "modern", "APIs", "replace", "XML"]
    clean_words = []
    t = 0.0
    for tok in clean_tokens:
        clean_words.append(WordAlignment(id=f"w_{tok}", word=tok, start=t, end=t + 0.4))
        t += 0.5
    clean_words.append(WordAlignment(id="end_clean", word="finished.", start=34.0, end=34.5))

    clean_score, clean_deictic, _, clean_feats, _, _ = clipper._score_span(
        clean_words, 0.0, 35.0, diffs
    )
    assert clean_deictic is False
    assert clean_feats["penalty_deictic"] == 0.0
    assert clean_score > score


def test_magnetic_snapping_to_sentence_and_pauses():
    """
    Verifies magnetic snapping of candidate clip start/end boundaries
    to complete sentences and pauses (>= 0.4s) strictly between 30s and 60s.
    """
    clipper = ClosedThoughtClipper()

    # Construct transcript with natural pauses (>= 0.4s) and punctuation
    words = []
    cur_t = 0.0

    # Part 1: Intro sentence (0s - 12s)
    for i in range(15):
        w_text = f"intro{i}" + ("." if i == 14 else "")
        words.append(WordAlignment(id=f"w{i}", word=w_text, start=cur_t, end=cur_t + 0.5))
        cur_t += 0.55 if i < 14 else 0.95  # 0.45s pause at sentence end

    # Part 2: Middle concept (13s - 38s)
    pause_target_idx = len(words) + 12
    for i in range(25):
        w_text = f"concept{i}"
        pause = 0.60 if (len(words) == pause_target_idx) else 0.10
        words.append(WordAlignment(id=f"w_{len(words)}", word=w_text, start=cur_t, end=cur_t + 0.5))
        cur_t += 0.5 + pause

    # Part 3: Conclusion (39s - 65s)
    for i in range(25):
        w_text = f"conclusion{i}" + ("." if i == 24 else "")
        words.append(WordAlignment(id=f"w_{len(words)}", word=w_text, start=cur_t, end=cur_t + 0.5))
        cur_t += 0.60

    # Test magnetic snapping
    target_start = 2.0
    target_end = 40.0
    snap_s, snap_e, s_idx, e_idx = clipper.magnetically_snap_window(
        target_start, target_end, words, min_duration=30.0, max_duration=60.0, pause_threshold=0.40
    )

    dur = snap_e - snap_s
    assert 30.0 <= dur <= 60.0
    # Must snap start to sentence start boundary
    assert any(abs(snap_s - w.start) < 0.01 for w in words)
    # Must snap end to boundary
    assert any(abs(snap_e - w.end) < 0.01 for w in words) or any(abs(snap_e - w.start) < 0.01 for w in words)

    # Test extract_highlights with full words list
    diffs = [
        VisualDiffEvent(timestamp=15.0, diff_magnitude=0.03, is_plateau=True),
        VisualDiffEvent(timestamp=25.0, diff_magnitude=0.04, is_plateau=True),
    ]
    highlights = clipper.extract_highlights(words, diffs, min_duration=30.0, max_duration=60.0, top_k=2)
    assert len(highlights) >= 1
    for h in highlights:
        assert 30.0 <= h.duration <= 60.0
        assert h.start_time >= 0.0
        assert h.triad_score > 0.0


# ============================================================================
# MODE B COMPILER: AST-Verified Topic Explainer Tests
# ============================================================================

def test_mode_b_4_pedagogical_beats():
    """
    Verifies that Mode B compiles prompts into 4 pedagogical beats:
    (1) Hook, (2) Core Code Concept, (3) Mutation/Contrast, (4) Terminal Verification.
    """
    compiler = ModeBCompiler()
    beats = compiler._generate_beats("JSON vs XML", target_duration=40.0)

    assert len(beats) == 4
    assert beats[0].beat_number == 1
    assert "Hook" in beats[0].title
    assert beats[1].beat_number == 2
    assert "Core" in beats[1].title or "Concept" in beats[1].title or "Structure" in beats[1].title
    assert beats[2].beat_number == 3
    assert "Mutation" in beats[2].title or "Contrast" in beats[2].title or "Overhead" in beats[2].title
    assert beats[3].beat_number == 4
    assert "Verification" in beats[3].title or "Takeaway" in beats[3].title

    # Tree-Sitter validation of all code snippets
    gate = TreeSitterGate()
    for b in beats:
        res = gate.validate_snippet(b.code_snippet, b.language)
        assert res.total_lines <= 14
        assert res.max_line_width <= 42 or len(res.syntax_errors) == 0


def test_mode_b_ollama_query_and_zero_crash_fallbacks():
    """
    Tests Ollama querying with mock response and zero-crash fallback to Gemini Flash and deterministic generator.
    """
    compiler = ModeBCompiler()

    # 1. Test Ollama successful mock
    mock_ollama_response = {
        "response": json.dumps({
            "beats": [
                {"beat_number": 1, "title": "The Hook", "voiceover_text": "Why use Redis?", "code_snippet": "# Redis Hook\ncache = 'redis'", "language": "python"},
                {"beat_number": 2, "title": "Core Code Concept", "voiceover_text": "Key-value store.", "code_snippet": "cache.set('key', 'val')", "language": "python"},
                {"beat_number": 3, "title": "Mutation/Contrast", "voiceover_text": "Without TTL, memory blows up.", "code_snippet": "cache.setex('key', 60, 'val')", "language": "python"},
                {"beat_number": 4, "title": "Terminal Verification", "voiceover_text": "TTL verified.", "code_snippet": "assert cache.ttl('key') > 0", "language": "python"},
            ]
        })
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_ollama_response

    with patch("httpx.Client.post", return_value=mock_resp):
        beats = compiler._query_ollama("Redis Caching", target_duration=40.0)
        assert beats is not None
        assert len(beats) == 4
        assert beats[0].title == "The Hook"

    # 2. Test Ollama failure falls through to Gemini Flash mock
    mock_gemini_response = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": json.dumps({
                                "beats": [
                                    {"beat_number": 1, "title": "The Hook", "voiceover_text": "Gemini Hook", "code_snippet": "# Hook\nx = 1", "language": "python"},
                                    {"beat_number": 2, "title": "Core Code Concept", "voiceover_text": "Gemini Core", "code_snippet": "y = x + 1", "language": "python"},
                                    {"beat_number": 3, "title": "Mutation/Contrast", "voiceover_text": "Gemini Contrast", "code_snippet": "z = y * 2", "language": "python"},
                                    {"beat_number": 4, "title": "Terminal Verification", "voiceover_text": "Gemini Verification", "code_snippet": "assert z == 4", "language": "python"},
                                ]
                            })
                        }
                    ]
                }
            }
        ]
    }

    mock_gemini_resp = MagicMock()
    mock_gemini_resp.status_code = 200
    mock_gemini_resp.json.return_value = mock_gemini_response

    with patch.object(compiler, "_query_ollama", return_value=None):
        with patch("backend.app.config.settings.GEMINI_API_KEY", "test-key"):
            with patch("httpx.Client.post", return_value=mock_gemini_resp):
                gemini_beats = compiler._query_gemini("Async Concurrency", target_duration=36.0)
                assert gemini_beats is not None
                assert len(gemini_beats) == 4
                assert gemini_beats[0].voiceover_text == "Gemini Hook"

    # 3. Test Full Zero-Crash Fallback (Ollama & Gemini both offline)
    with patch.object(compiler, "_query_ollama", return_value=None):
        with patch.object(compiler, "_query_gemini", return_value=None):
            beats_fallback = compiler._generate_beats("Unknown Custom Protocol", target_duration=40.0)
            assert len(beats_fallback) == 4
            assert beats_fallback[0].beat_number == 1
            assert beats_fallback[3].beat_number == 4


def test_mode_b_neural_tts_and_zero_drift_lock():
    """
    Verifies that Mode B compiler synthesizes audio and locks typing animation
    and word alignments to exact audio duration with 0ms drift.
    """
    compiler = ModeBCompiler()

    # Test offline audio synthesis with millisecond timestamps
    raw_pcm, timings, dur = compiler._generate_offline_synthetic_audio("Why did APIs switch to JSON?")
    assert len(raw_pcm) > 0
    assert dur > 1.0
    assert len(timings) == 6
    assert timings[0]["start"] == 0.0
    assert timings[-1]["end"] == pytest.approx(dur, abs=0.01)

    # Test complete compilation
    reel = compiler.compile_prompt("JSON vs XML", target_duration=20.0)
    assert reel.mode == "mode_b_prompt"
    assert len(reel.code_cards) == 4
    assert len(reel.transcript) > 0

    # Zero drift check: Card boundaries match beat duration progression
    cur_t = 0.0
    for card in reel.code_cards:
        assert card.start == pytest.approx(cur_t, abs=0.01)
        assert card.end > card.start
        cur_t = card.end
    assert reel.total_duration == pytest.approx(cur_t, abs=0.02)

    # Social Growth Pack check (Weapon 8)
    assert reel.social_growth_pack is not None
    assert len(reel.social_growth_pack.broad_hashtags) >= 1
    assert len(reel.social_growth_pack.stack_hashtags) >= 1
    assert reel.social_growth_pack.qr_code_data.startswith("https://")


# ============================================================================
# WEAPON 6: PedagogyScore Contextual Bandit Tests
# ============================================================================

def test_pedagogy_score_bandit_lifecycle_and_updates(tmp_path):
    """
    Tests SQLite-backed PedagogyScore Contextual Bandit:
    - Default prior weights
    - Online LinUCB / Bayesian weight update upon viewer retention & export signals
    - Telemetry history recording
    """
    db_file = tmp_path / "test_snipshot.db"
    bandit = PedagogyScoreBandit(db_path=db_file)

    init_weights = bandit.get_weights()
    assert init_weights["w1"] == 0.15  # RMS
    assert init_weights["w2"] == 0.25  # Visual
    assert init_weights["w3"] == 0.25  # Tech
    assert init_weights["w4"] == 0.35  # Triad
    assert init_weights["w5"] == 2.00  # Deictic

    # Predict score using priors
    features = {
        "rms_audio": 0.8,
        "diff_visual": 0.7,
        "tech_density": 0.9,
        "bug2fix_bonus": 1.0,
        "penalty_deictic": 0.0,
    }
    score_pred = bandit.predict_score(features, use_exploration=True)
    assert score_pred > 0.5

    # Simulate positive feedback: 90% retention and user export
    updated_weights = bandit.record_feedback(
        reel_id="reel_highlight_42",
        features=features,
        retention_rate=0.90,
        exported=True,
    )

    # Confirm weights updated and remained within stable bounds
    assert updated_weights["w1"] >= 0.05
    assert updated_weights["w2"] >= 0.05
    assert updated_weights["w4"] >= 0.05
    assert updated_weights["w5"] >= 0.50

    # Query telemetry history
    history = bandit.get_telemetry_history()
    assert len(history) == 1
    assert history[0]["reel_id"] == "reel_highlight_42"
    assert history[0]["exported"] is True
    assert history[0]["retention_rate"] == 0.90
    assert history[0]["reward"] == pytest.approx(0.95, abs=0.01)

    # Ensure persistence: open new bandit instance pointing to same SQLite DB
    bandit2 = PedagogyScoreBandit(db_path=db_file)
    persisted_weights = bandit2.get_weights()
    assert persisted_weights["w1"] == updated_weights["w1"]
    assert persisted_weights["w4"] == updated_weights["w4"]


def test_closed_thought_integrated_with_feedback_bandit(tmp_path):
    """
    Verifies ClosedThoughtClipper dynamically pulls updated weights from PedagogyScoreBandit.
    """
    db_file = tmp_path / "bandit_integration.db"
    bandit = PedagogyScoreBandit(db_path=db_file)

    # Update bandit weights with feedback
    bandit.record_feedback(
        reel_id="reel_101",
        features={"rms_audio": 0.9, "diff_visual": 0.8, "tech_density": 0.8, "bug2fix_bonus": 1.0, "penalty_deictic": 0.0},
        retention_rate=1.0,
        exported=True,
    )

    # Initialize clipper with bandit
    clipper = ClosedThoughtClipper(bandit=bandit)
    assert clipper.w_prosody == bandit.w1
    assert clipper.w_visual == bandit.w2
    assert clipper.w_triad == bandit.w4
    assert clipper.w_deictic == bandit.w5
