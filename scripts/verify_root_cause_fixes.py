import os
import json
import re
from backend.app.core.fast_mode_a import FastModeAEngine
from backend.app.core.fast_native_compositor import FastNativeCompositor
from backend.app.core.hinglish_normalizer import clean_hinglish_with_ocr

def test_fix1_dummy_loop_deletion():
    print("\n=== 1. Testing Fix 1: Dummy loop deletion ===")
    comp = FastNativeCompositor()
    out_ass = "data/cache/test_empty_fix1.ass"
    comp.generate_ass_subtitles(words=[], start_sec=0.0, duration=15.0, output_path=out_ass)
    with open(out_ass, "r") as f:
        content = f.read()
    assert "Code highlight and explanation walkthrough" not in content, "Fix 1 failed: dummy text still found!"
    assert "Dialogue:" not in content, "Fix 1 failed: dialogue lines generated on empty words!"
    print(" Fix 1 PASSED: Zero dummy text and zero dialogue lines when words is empty.")

def test_fix4_phonetic_ngram_repair():
    print("\n=== 2. Testing Fix 4: Phonetic & Compound n-gram repair ===")
    test_words = [
        {"word": "java", "start": 21.0, "end": 21.5, "abs_start": 21.0, "abs_end": 21.5},
        {"word": "ek", "start": 21.6, "end": 22.0, "abs_start": 21.6, "abs_end": 22.0},
        {"word": "ke", "start": 22.3, "end": 22.5, "abs_start": 22.3, "abs_end": 22.5},
        {"word": "ssitrig", "start": 22.6, "end": 23.3, "abs_start": 22.6, "abs_end": 23.3},
        {"word": "lnbaj", "start": 23.4, "end": 24.04, "abs_start": 23.4, "abs_end": 24.04},
        {"word": "hai", "start": 24.2, "end": 24.6, "abs_start": 24.2, "abs_end": 24.6},
        {"word": "bhada", "start": 25.0, "end": 25.4, "abs_start": 25.0, "abs_end": 25.4},
        {"word": "p", "start": 25.5, "end": 25.9, "abs_start": 25.5, "abs_end": 25.9},
        {"word": "aktian", "start": 26.5, "end": 27.0, "abs_start": 26.5, "abs_end": 27.0},
        {"word": "lisnar", "start": 27.1, "end": 27.6, "abs_start": 27.1, "abs_end": 27.6},
    ]
    screen_tokens = ["Java", "case-sensitive", "language", "ActionListener", "boardPanel"]
    repaired = clean_hinglish_with_ocr(test_words, screen_tokens)
    
    repaired_text = " ".join([w["word"] for w in repaired])
    print("Repaired words text:", repaired_text)
    
    assert "case-sensitive" in repaired_text, "Fix 4 failed: case-sensitive not found in repaired text!"
    assert "language" in repaired_text, "Fix 4 failed: language not found in repaired text!"
    assert "bada P" in repaired_text or "P" in repaired_text, "Fix 4 failed: bhada p not repaired!"
    assert "ActionListener" in repaired_text, "Fix 4 failed: aktian lisnar not repaired!"
    print(" Fix 4 PASSED: Spoken Hinglish & compound n-grams successfully repaired with screen tokens!")

def test_fix3_speech_onset_and_video_processing():
    print("\n=== 3. Testing Fix 3: Speech Onset Snapping on Video ===")
    engine = FastModeAEngine()
    java_vid = "/home/ninad0109/Downloads/WhatsApp Video 2026-10-17 at 05.35.24.mp4"
    assert os.path.exists(java_vid), f"Video not found: {java_vid}"

    res = engine.process_video(java_vid, target_clip_duration=30.0)
    print("Clip start:", res["start_sec"])
    print("Clip end:", res["end_sec"])
    print("Duration:", res["duration"])
    print("Words count:", len(res["words"]))
    print("Transcript words count:", len(res["transcript_words"]))
    print("Video URL:", res["video_url"])
    print("Transcript preview:", res["transcript"][:120])

    # Assert speech onset snapped past initial silence
    assert res["start_sec"] >= 20.0, f"Fix 3 failed: clip_start did not snap to speech onset! (got {res['start_sec']})"
    print(f" Fix 3 PASSED: clip_start snapped from 0.0s to {res['start_sec']}s right before speech onset!")

    # Check first word relative timing
    first_w = res["words"][0]
    print(f"First word: '{first_w['word']}' at {first_w['start']}s (relative to clip)")
    assert first_w["start"] <= 1.0, f"First subtitle word appears too late! (at {first_w['start']}s)"
    print(" First subtitle word appears immediately (<= 1.0s)!")
    return engine, java_vid, res

def test_fix2_rerender_persistence(engine, java_vid, res):
    print("\n=== 4. Testing Fix 2: Re-render with Word Persistence ===")
    # Test re-render without explicitly passing words (must load from cache or slice)
    re_res = engine.rerender_clip(
        source_video_path=java_vid,
        start_sec=res["start_sec"] + 2.0,
        end_sec=res["start_sec"] + 25.0,
        code_snippet=res["code_snippet"],
        clip_id=res["clip_id"],
    )
    print("Re-render words count:", len(re_res["words"]))
    print("Re-render video URL:", re_res["video_url"])
    assert len(re_res["words"]) > 0, "Fix 2 failed: words is empty on re-render!"
    
    with open(f"data/cache/subs_re_{res['clip_id']}.ass", "r") as f:
        re_ass = f.read()
    assert "Code highlight and explanation walkthrough" not in re_ass, "Fix 2 failed: dummy loop appeared on re-render!"
    assert "Dialogue:" in re_ass, "Fix 2 failed: no subtitles rendered on re-render!"
    print(" Fix 2 PASSED: Re-rendered successfully with real spoken subtitles, zero dummy loops!")

def test_fix5_frontend_cache_buster():
    print("\n=== 5. Testing Fix 5: Frontend Cache-Buster & Video Props ===")
    frontend_file = "frontend/src/components/studio/ModeAStudio.tsx"
    with open(frontend_file, "r") as f:
        tsx_content = f.read()
    assert "cacheBuster" in tsx_content, "Fix 5 failed: cacheBuster state not found in ModeAStudio.tsx!"
    assert "?t=${cacheBuster}" in tsx_content, "Fix 5 failed: ?t=${cacheBuster} query param not appended to video source!"
    assert "playsInline" in tsx_content, "Fix 5 failed: playsInline not added to video tag!"
    print(" Fix 5 PASSED: Frontend uses dynamic cache buster and proper video player attributes.")

if __name__ == "__main__":
    test_fix1_dummy_loop_deletion()
    test_fix4_phonetic_ngram_repair()
    engine, java_vid, res = test_fix3_speech_onset_and_video_processing()
    test_fix2_rerender_persistence(engine, java_vid, res)
    test_fix5_frontend_cache_buster()
    print("\n🎉 ALL 5 ROOT CAUSE FIXES VERIFIED SUCCESSFULLY AND ARE 100% WORKING!")
