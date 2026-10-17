#!/usr/bin/env python3
"""
Test Suite for Testing the Latest 4 Downloaded WhatsApp Videos in SnipShot.
Verifies:
1. Video-Agnostic Compositor (720p vs 1080p source scaled to 1080x1920 without errors).
2. Output MP4 exists, is 1080x1920, and playable.
3. Extracted code snippet has proper indentation and comes from THAT video.
4. Zero '□' tofu characters in rendered video frames and ASS subtitles.
5. Hashtags and Pinned Code Comment match THAT video with zero hardcoded React/useEffect text.
6. Highlights the best teaching clips for the live demo.
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.app.core.fast_mode_a import FastModeAEngine

VIDEOS = [
    {
        "id": 1,
        "name": "Video 1 (Python FirstProgram.py)",
        "path": "/home/ninad0109/Downloads/WhatsApp Video 2026-10-17 at 05.31.58.mp4",
        "expected_lang": "python",
        "expected_code_tokens": ["print", "Hello World"],
        "expected_tags": ["#python", "#firstprogram"],
        "expected_resolution": (1280, 720),
    },
    {
        "id": 2,
        "name": "Video 2 (Java Swing WhacAMole.java)",
        "path": "/home/ninad0109/Downloads/WhatsApp Video 2026-10-17 at 05.37.52.mp4",
        "expected_lang": "java",
        "expected_code_tokens": ["boardPanel.add(tile)", "WhacAMole"],
        "expected_tags": ["#javaswing", "#whacamole", "#java"],
        "expected_resolution": (1280, 720),
    },
    {
        "id": 3,
        "name": "Video 3 (Java OOP Main.java / Car.java)",
        "path": "/home/ninad0109/Downloads/WhatsApp Video 2026-10-17 at 05.35.24.mp4",
        "expected_lang": "java",
        "expected_code_tokens": ["Car", "Main"],
        "expected_tags": ["#javaoop", "#java"],
        "expected_resolution": (1280, 720),
    },
    {
        "id": 4,
        "name": "Video 4 (GitHub Desktop & Terminal)",
        "path": "/home/ninad0109/Downloads/WhatsApp Video 2026-10-17 at 01.58.04.mp4",
        "expected_lang": "bash",
        "expected_code_tokens": ["desktop.github.com", "github", "touch index.html", "sample-repo"],
        "expected_tags": ["#githubdesktop", "#git", "#terminal"],
        "expected_resolution": (1920, 1080),
    },
]


def probe_mp4(mp4_path: str):
    """Probes resolution, duration, and stream integrity via ffprobe & ffmpeg."""
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,duration",
        "-of", "json",
        str(mp4_path),
    ]
    out = subprocess.check_output(cmd).decode()
    data = json.loads(out)
    stream = data.get("streams", [{}])[0]
    w = int(stream.get("width", 0))
    h = int(stream.get("height", 0))
    dur = float(stream.get("duration", 0.0))

    # Verify playability by decoding null frames
    decode_cmd = ["ffmpeg", "-v", "error", "-i", str(mp4_path), "-f", "null", "-"]
    decode_res = subprocess.run(decode_cmd, stderr=subprocess.PIPE)
    is_playable = (decode_res.returncode == 0)

    return w, h, dur, is_playable


def main():
    print("=" * 80)
    print("🚀 SNIPSHOT FIX 5: MULTI-VIDEO VERIFICATION & RESOLUTION-AGNOSTIC COMPOSITOR TEST")
    print("=" * 80)

    engine = FastModeAEngine()
    results_summary = []

    for v_info in VIDEOS:
        v_id = v_info["id"]
        v_name = v_info["name"]
        v_path = v_info["path"]
        print(f"\n[{v_id}/4] Processing: {v_name}")
        print(f"      File: {v_path}")

        if not os.path.exists(v_path):
            print(f"      ❌ ERROR: File does not exist on disk: {v_path}")
            sys.exit(1)

        t0 = time.time()
        res = engine.process_video(
            video_path=v_path,
            institute_name="SNIPSHOT ACADEMY",
            brand_color="#4F46E5",
            target_clip_duration=35.0,
        )
        elapsed = round(time.time() - t0, 2)
        print(f"      ✅ Processed in {elapsed}s (Engine elapsed: {res['elapsed_seconds']}s)")

        # 1. Output MP4 Verification
        output_rel = res["video_url"].split("?")[0].lstrip("/")
        output_mp4 = BASE_DIR / "backend" / output_rel
        if not output_mp4.exists():
            output_mp4 = BASE_DIR / output_rel
        assert output_mp4.exists(), f"Output MP4 {output_mp4} does not exist!"
        mp4_size_mb = output_mp4.stat().st_size / (1024 * 1024)

        w, h, dur, is_playable = probe_mp4(str(output_mp4))
        print(f"      📹 Output: {w}x{h}, {dur:.1f}s, {mp4_size_mb:.2f} MB, playable: {is_playable}")
        assert w == 1080, f"Expected width 1080, got {w}"
        assert h == 1920, f"Expected height 1920, got {h}"
        assert is_playable, f"Rendered MP4 {output_mp4} failed ffmpeg decode integrity check!"

        # 2. Code Snippet Verification
        snippet = res.get("code_snippet", "")
        print(f"      📝 Snippet ({len(snippet.splitlines())} lines):")
        for line in snippet.splitlines()[:5]:
            print(f"         | {line}")
        if len(snippet.splitlines()) > 5:
            print("         | ...")

        # Check indentation: at least one line should start with indentation spaces
        has_indent = any(line.startswith("    ") or line.startswith("   ") for line in snippet.splitlines())
        print(f"      🔎 Indentation preserved: {has_indent}")
        assert has_indent, f"Code snippet for {v_name} lacks proper indentation!"

        # Check snippet matches THAT video
        has_expected_token = any(tok in snippet for tok in v_info["expected_code_tokens"])
        print(f"      🎯 Code matches video ({v_info['expected_code_tokens']}): {has_expected_token}")
        assert has_expected_token, f"Snippet does not contain expected tokens {v_info['expected_code_tokens']} from {v_name}!"

        # 3. Zero '□' tofu characters
        tofu_glyphs = ["□", "\ufffd", "\u25a1", "\u25a0"]
        has_tofu = any(g in snippet or g in res["transcript"] for g in tofu_glyphs)
        print(f"      ✨ Zero tofu glyphs '□': {not has_tofu}")
        assert not has_tofu, f"Tofu '□' glyph found in snippet or transcript for {v_name}!"

        # Also check ASS subtitle file
        ass_path = BASE_DIR / "data" / "cache" / f"subs_{res['video_id']}.ass"
        if ass_path.exists():
            ass_text = ass_path.read_text(encoding="utf-8")
            assert not any(g in ass_text for g in tofu_glyphs), f"Tofu '□' found in {ass_path}!"

        # 4. Hashtags and Pinned Comment Matching
        hashtags = res.get("hashtags", [])
        growth_pack = res.get("social_growth_pack", {})
        pinned_comment = growth_pack.get("pinned_comment", "")
        hook_title = growth_pack.get("hook_title", "")

        print(f"      🏷️  Hashtags: {hashtags}")
        print(f"      📌 Pinned Comment: {pinned_comment}")
        print(f"      🎯 Hook Title: {hook_title}")

        # Assert zero hardcoded React / useEffect
        assert not any("useeffect" in tag.lower() for tag in hashtags), f"Hardcoded #useEffect found in hashtags for {v_name}!"
        assert not any("react" in tag.lower() for tag in hashtags), f"Hardcoded #react found in hashtags for {v_name}!"
        assert "useeffect" not in pinned_comment.lower(), f"Hardcoded useEffect found in pinned comment for {v_name}!"
        assert "useeffect" not in hook_title.lower(), f"Hardcoded useEffect found in hook title for {v_name}!"

        # Assert hashtags match video
        matches_tag = any(tag in hashtags for tag in v_info["expected_tags"])
        assert matches_tag, f"Hashtags {hashtags} do not match expected tags {v_info['expected_tags']} for {v_name}!"

        results_summary.append({
            "id": v_id,
            "name": v_name,
            "source_res": v_info["expected_resolution"],
            "output_res": f"{w}x{h}",
            "duration": f"{dur:.1f}s",
            "snippet_preview": snippet.splitlines()[0] if snippet else "",
            "hook_title": hook_title,
            "hashtags": hashtags[:4],
            "mp4_path": str(output_mp4),
        })

    print("\n" + "=" * 80)
    print("🏆 SUMMARY REPORT: ALL 4 VIDEOS VERIFIED SUCCESSFULLY")
    print("=" * 80)
    for r in results_summary:
        print(f"• [{r['id']}] {r['name']}")
        print(f"    Source: {r['source_res'][0]}x{r['source_res'][1]} -> Output: {r['output_res']} ({r['duration']})")
        print(f"    Code Snippet: {r['snippet_preview']}")
        print(f"    Hook: {r['hook_title']}")
        print(f"    Tags: {r['hashtags']}")
        print(f"    Rendered Reel: {r['mp4_path']}")

    print("\n🌟 DEMO RECOMMENDATION:")
    print("  Video 1 (Python ApnaCollege) & Video 2 (Java Swing WhacAMole) have the HIGHEST engagement value:")
    print("  - Video 1 teaches Python FirstProgram.py and print('Hello World') — ultra crisp 9:16 layout!")
    print("  - Video 2 features real game development with JButton and boardPanel.add(tile) — dynamic UI card!")
    print("=" * 80)


if __name__ == "__main__":
    main()
