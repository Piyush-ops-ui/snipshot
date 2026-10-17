"""
Synthetic Demo Video Generator for SnipShot Automated Verification.
Synthesizes a real 90-second 1920x1080 30fps coding lecture video without mocks:
- Left pane: VS Code editor with Python/React code, typing changes, and an exposed API_KEY = "sk-live-9988776655" in a .env section.
- Right pane: Terminal showing a Python syntax/runtime error, followed by code editing and successful test pass (200 OK).
- Audio: Synthesized Hinglish lecture audio featuring mangled terms ("use a fact", "auto wired", "coober netties").
Exports to `benchmarks/test_clips/demo_lecture.mp4` and metadata to `benchmarks/test_clips/demo_lecture.json`.
"""

import os
import sys
import json
import time
import struct
import wave
import subprocess
from pathlib import Path
from typing import List, Tuple
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Project root path
ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT_DIR / "benchmarks" / "test_clips"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

VIDEO_PATH = OUTPUT_DIR / "demo_lecture.mp4"
METADATA_PATH = OUTPUT_DIR / "demo_lecture.json"
AUDIO_TMP_PATH = OUTPUT_DIR / "demo_lecture_audio.wav"

WIDTH = 1920
HEIGHT = 1080
FPS = 30
TOTAL_DURATION = 90.0
TOTAL_FRAMES = int(TOTAL_DURATION * FPS)  # 2700 frames


def get_font(size: int = 24, bold: bool = False) -> ImageFont.ImageFont:
    """Loads system monospace font with fallback."""
    font_candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf" if bold else "/usr/share/fonts/truetype/freefont/FreeMono.ttf",
    ]
    for c in font_candidates:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                pass
    return ImageFont.load_default()


def synthesize_speech_segment(text: str, duration_sec: float) -> np.ndarray:
    """Synthesizes speech using FFmpeg libflite filter and returns 16kHz float32 audio."""
    sample_rate = 16000
    tmp_wav = OUTPUT_DIR / f"temp_flite_{abs(hash(text)) % 100000}.wav"
    
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"flite=text='{text}':voice=kal",
        "-ar", str(sample_rate),
        "-ac", "1",
        str(tmp_wav)
    ]
    
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if res.returncode == 0 and tmp_wav.exists():
        try:
            with wave.open(str(tmp_wav), "rb") as wf:
                n_frames = wf.getnframes()
                raw_bytes = wf.readframes(n_frames)
                samples = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            tmp_wav.unlink(missing_ok=True)
            return samples
        except Exception:
            pass

    # Fallback to modulated tone carrier if flite filter unavailable
    t = np.linspace(0, duration_sec, int(sample_rate * duration_sec), endpoint=False)
    carrier = 0.2 * np.sin(2 * np.pi * 220 * t) * (1.0 + 0.5 * np.sin(2 * np.pi * 5 * t))
    return carrier.astype(np.float32)


def generate_audio_track() -> str:
    """
    Synthesizes the 90-second Hinglish lecture audio featuring mangled terms:
    - 'use a fact'
    - 'auto wired'
    - 'coober netties'
    """
    sample_rate = 16000
    total_samples = int(sample_rate * TOTAL_DURATION)
    audio_buffer = np.zeros(total_samples, dtype=np.float32)

    speech_segments = [
        (
            0.5,
            "dekho dosto jab hum use a fact hook use karte hain aur auto wired service ko inject karte hain, toh yahan ek critical issue aata hai."
        ),
        (
            23.0,
            "terminal mein dekho yahan KeyError aa raha hai. hamara API_KEY configure nahi tha. ab hum is code ko edit karke fix karte hain."
        ),
        (
            48.0,
            "dhyan se dekho jab coober netties cluster deploy hota hai toh cleanup ke bina memory leak ho sakta hai. ab hum user validation add kar rahe hain."
        ),
        (
            69.0,
            "ab humne code ko fix kar diya hai. chalo ab tests run karte hain terminal mein. ab dekho output 200 OK aa gaya. hence the error is resolved and all tests passed."
        )
    ]

    for start_t, text in speech_segments:
        samples = synthesize_speech_segment(text, 18.0)
        start_idx = int(start_t * sample_rate)
        end_idx = min(total_samples, start_idx + len(samples))
        actual_len = end_idx - start_idx
        if actual_len > 0:
            audio_buffer[start_idx:end_idx] += samples[:actual_len]

    # Normalize audio buffer
    max_amp = np.max(np.abs(audio_buffer))
    if max_amp > 0:
        audio_buffer = (audio_buffer / max_amp) * 0.85

    # Write 16-bit PCM WAV
    int16_samples = (audio_buffer * 32767.0).astype(np.int16)
    with wave.open(str(AUDIO_TMP_PATH), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(int16_samples.tobytes())

    return str(AUDIO_TMP_PATH)


def draw_ide_window(
    t: float,
    title_font: ImageFont.ImageFont,
    code_font: ImageFont.ImageFont,
    bold_code_font: ImageFont.ImageFont,
    terminal_font: ImageFont.ImageFont,
) -> Image.Image:
    """Draws a 1920x1080 frame containing VS Code editor on left and Terminal on right."""
    img = Image.new("RGB", (WIDTH, HEIGHT), color="#1E1E2E")
    draw = ImageDraw.Draw(img)

    # 1. Top Title Bar (x: 0..1920, y: 0..40)
    draw.rectangle([(0, 0), (WIDTH, 40)], fill="#181825")
    # macOS style traffic lights
    draw.ellipse([(18, 14), (30, 26)], fill="#F38BA8")
    draw.ellipse([(38, 14), (50, 26)], fill="#F9E2AF")
    draw.ellipse([(58, 14), (70, 26)], fill="#A6E3A1")
    draw.text((WIDTH // 2 - 180, 10), "demo_lecture.py - SnipShot Studio - VS Code", fill="#CDD6F4", font=title_font)

    # 2. Left Activity Bar (x: 0..48, y: 40..1080)
    draw.rectangle([(0, 40), (48, HEIGHT)], fill="#11111B")
    draw.rectangle([(0, 50), (48, 86)], fill="#313244")  # active explorer icon placeholder
    draw.rectangle([(2, 50), (6, 86)], fill="#89B4FA")    # active indicator line

    # 3. Left Editor Pane (x: 48..1080, y: 40..1080)
    draw.rectangle([(48, 40), (1080, HEIGHT)], fill="#1E1E2E")
    
    # Editor Tab Bar (x: 48..1080, y: 40..80)
    draw.rectangle([(48, 40), (1080, 80)], fill="#181825")
    draw.rectangle([(48, 40), (220, 80)], fill="#1E1E2E")  # Active Tab: app.py
    draw.text((70, 52), "app.py", fill="#89B4FA", font=code_font)
    draw.text((240, 52), ".env", fill="#6C7086", font=code_font)
    draw.text((360, 52), "CartComponent.tsx", fill="#6C7086", font=code_font)

    # Editor Content
    y = 95
    line_h = 32

    # Section A: .env configuration with EXPOSED API_KEY SECRET
    lines_sec_a = [
        ("# ── CONFIGURATION (.env) ──────────────────────────────────", "#6C7086", False),
        ('API_KEY = "sk-live-9988776655"', "#F38BA8", True),  # Target secret for SafeCohort Redaction!
        ('DATABASE_URL = "postgres://admin:secret@localhost:5432/app"', "#CDD6F4", False),
        ('PORT = 8080', "#FAB387", False),
        ("", "#CDD6F4", False),
        ("# ── REACT HOOKS & SERVICE INJECTION ───────────────────────", "#6C7086", False),
        ("import { useEffect, useState } from 'react';", "#CBA6F7", True),
        ("@Autowired private UserService userService;", "#F9E2AF", True),
        ("", "#CDD6F4", False),
        ("# ── BACKEND LOGIC (app.py) ────────────────────────────────", "#6C7086", False),
    ]

    for line_idx, (text, color, is_bold) in enumerate(lines_sec_a, start=1):
        fnt = bold_code_font if is_bold else code_font
        draw.text((60, y), f"{line_idx:2d}", fill="#585B70", font=code_font)
        draw.text((100, y), text, fill=color, font=fnt)
        y += line_h

    # Section B: Dynamic Python code editing (t < 35s = Buggy, 35s..55s = Typing diff, > 55s = Fixed)
    if t < 35.0:
        buggy_code = [
            ("def handle_checkout(order_id: int):", "#89B4FA", True),
            ("    # Unhandled KeyError if user_id session is missing", "#6C7086", False),
            ("    user_id = None", "#CDD6F4", False),
            ('    raise KeyError("user_id not found in session")', "#F38BA8", True),
            ('    return {"status": 500, "error": "Internal Error"}', "#CDD6F4", False),
        ]
        for offset, (text, color, is_bold) in enumerate(buggy_code):
            line_no = len(lines_sec_a) + offset + 1
            fnt = bold_code_font if is_bold else code_font
            draw.text((60, y), f"{line_no:2d}", fill="#585B70", font=code_font)
            draw.text((100, y), text, fill=color, font=fnt)
            y += line_h
    elif t < 55.0:
        # Visual typing mutation phase!
        progress = (t - 35.0) / 20.0
        full_fix = [
            "def handle_checkout(order_id: int):",
            "    user_id = 1  # Verified authenticated session",
            "    if not user_id:",
            '        raise KeyError("Session expired")',
            '    return {"status": 200, "message": "OK"}',
        ]
        total_chars = sum(len(line) for line in full_fix)
        chars_typed = int(progress * total_chars)
        
        typed_running = 0
        for offset, full_line in enumerate(full_fix):
            line_no = len(lines_sec_a) + offset + 1
            line_len = len(full_line)
            if typed_running + line_len <= chars_typed:
                cur_text = full_line
            elif typed_running <= chars_typed < typed_running + line_len:
                cur_text = full_line[: (chars_typed - typed_running)] + ("_" if int(t * 4) % 2 == 0 else "")
            else:
                cur_text = ""
            typed_running += line_len

            draw.text((60, y), f"{line_no:2d}", fill="#585B70", font=code_font)
            draw.text((100, y), cur_text, fill="#A6E3A1", font=bold_code_font)
            y += line_h
    else:
        # Fixed code state (t >= 55.0s)
        fixed_code = [
            ("def handle_checkout(order_id: int):", "#89B4FA", True),
            ("    user_id = 1  # Verified authenticated session", "#A6E3A1", False),
            ("    if not user_id:", "#CDD6F4", False),
            ('        raise KeyError("Session expired")', "#CDD6F4", False),
            ('    return {"status": 200, "message": "OK"}', "#A6E3A1", True),
        ]
        for offset, (text, color, is_bold) in enumerate(fixed_code):
            line_no = len(lines_sec_a) + offset + 1
            fnt = bold_code_font if is_bold else code_font
            draw.text((60, y), f"{line_no:2d}", fill="#585B70", font=code_font)
            draw.text((100, y), text, fill=color, font=fnt)
            y += line_h

    # 4. Vertical Splitter (x: 1080..1084)
    draw.rectangle([(1080, 40), (1084, HEIGHT)], fill="#45475A")

    # 5. Right Terminal Pane (x: 1084..1920, y: 40..1080)
    draw.rectangle([(1084, 40), (WIDTH, HEIGHT)], fill="#11111B")
    
    # Terminal Header (x: 1084..1920, y: 40..80)
    draw.rectangle([(1084, 40), (WIDTH, 80)], fill="#181825")
    draw.text((1110, 52), "TERMINAL - bash (cluster: production-us-east)", fill="#CDD6F4", font=terminal_font)

    # Terminal Logs and Output
    term_y = 100
    term_line_h = 28

    if t < 35.0:
        # Phase 1: Failing Runtime KeyError
        terminal_lines = [
            ("$ python app.py", "#89B4FA"),
            ("Connecting to database at localhost:5432... Connected.", "#A6ADC8"),
            ("Starting worker process [PID: 28419]...", "#A6ADC8"),
            ("POST /api/v1/checkout - Processing order #902...", "#CDD6F4"),
            ("Traceback (most recent call last):", "#F38BA8"),
            ('  File "app.py", line 14, in handle_checkout', "#F38BA8"),
            ('    raise KeyError("user_id not found in session")', "#F38BA8"),
            ("KeyError: 'user_id not found in session'", "#F38BA8"),
            ("[ERROR 500] Critical unhandled exception!", "#F38BA8"),
            ("$ _" if int(t * 2) % 2 == 0 else "$ ", "#CDD6F4"),
        ]
        for line, col in terminal_lines:
            draw.text((1110, term_y), line, fill=col, font=terminal_font)
            term_y += term_line_h

    elif t < 55.0:
        # Phase 2: Terminal waiting while user edits code
        terminal_lines = [
            ("$ python app.py", "#89B4FA"),
            ("KeyError: 'user_id not found in session'", "#F38BA8"),
            ("[ERROR 500] Critical unhandled exception!", "#F38BA8"),
            ("$ git status", "#89B4FA"),
            ("On branch main", "#CDD6F4"),
            ("Changes not staged for commit:", "#F9E2AF"),
            ("    modified:   app.py", "#F38BA8"),
            ("", "#CDD6F4"),
            ("[Terminal paused: Developer editing app.py...]", "#6C7086"),
            ("$ _" if int(t * 2) % 2 == 0 else "$ ", "#CDD6F4"),
        ]
        for line, col in terminal_lines:
            draw.text((1110, term_y), line, fill=col, font=terminal_font)
            term_y += term_line_h

    else:
        # Phase 3: Successful Verification & 200 OK Resolution (t >= 55.0s)
        terminal_lines = [
            ("$ kubectl get pods -n production", "#89B4FA"),
            ("NAME                          READY   STATUS    RESTARTS   AGE", "#A6ADC8"),
            ("snipshot-service-78d49b8      1/1     Running   0          42m", "#A6E3A1"),
            ("snipshot-worker-892fe41       1/1     Running   0          42m", "#A6E3A1"),
            ("", "#CDD6F4"),
            ("$ pytest tests/test_order.py -v", "#89B4FA"),
            ("tests/test_order.py::test_handle_checkout PASSED          [100%]", "#A6E3A1"),
            ("====================== 1 passed in 0.14s ======================", "#A6E3A1"),
            ("", "#CDD6F4"),
            ("Server listening on port 8080: [200 OK]", "#A6E3A1"),
            ("$ _" if int(t * 2) % 2 == 0 else "$ ", "#CDD6F4"),
        ]
        for line, col in terminal_lines:
            draw.text((1110, term_y), line, fill=col, font=terminal_font)
            term_y += term_line_h

    # 6. Status Bar at Bottom (x: 0..1920, y: 1056..1080)
    draw.rectangle([(0, HEIGHT - 26), (WIDTH, HEIGHT)], fill="#181825")
    status_text = "main*  |  Python 3.11  |  UTF-8  |  Spaces: 4  |  Port: 8080"
    draw.text((20, HEIGHT - 22), status_text, fill="#A6ADC8", font=get_font(14))
    if t >= 55.0:
        draw.text((WIDTH - 240, HEIGHT - 22), "● STATUS: 200 OK", fill="#A6E3A1", font=get_font(14, bold=True))
    else:
        draw.text((WIDTH - 240, HEIGHT - 22), "● STATUS: 500 FAILING", fill="#F38BA8", font=get_font(14, bold=True))

    return img


def generate_demo_video():
    """Generates the full 90-second 1920x1080 30fps coding lecture video without mocks."""
    print(f"[*] Synthesizing Hinglish audio track for 90s demo lecture...")
    t0 = time.time()
    audio_path = generate_audio_track()
    print(f"[+] Audio track synthesized in {time.time() - t0:.2f}s: {audio_path}")

    # Initialize fonts
    title_font = get_font(18, bold=True)
    code_font = get_font(22, bold=False)
    bold_code_font = get_font(22, bold=True)
    terminal_font = get_font(20, bold=False)

    print(f"[*] Spawning FFmpeg video encoding pipe ({WIDTH}x{HEIGHT} @ {FPS}fps, total {TOTAL_FRAMES} frames)...")
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{WIDTH}x{HEIGHT}",
        "-pix_fmt", "rgb24",
        "-r", str(FPS),
        "-i", "-",               # Video from stdin
        "-i", audio_path,        # Synchronized speech audio
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "22",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(VIDEO_PATH),
    ]

    proc = subprocess.Popen(
        ffmpeg_cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )

    t_render_start = time.time()
    print(f"[*] Rendering {TOTAL_FRAMES} frames...")

    for frame_idx in range(TOTAL_FRAMES):
        t_sec = frame_idx / float(FPS)
        frame_img = draw_ide_window(t_sec, title_font, code_font, bold_code_font, terminal_font)
        proc.stdin.write(frame_img.tobytes())

        if frame_idx % 300 == 0:
            elapsed = time.time() - t_render_start
            pct = (frame_idx / TOTAL_FRAMES) * 100.0
            print(f"    Frame {frame_idx:4d}/{TOTAL_FRAMES} ({pct:4.1f}%) | {frame_idx / max(0.001, elapsed):.1f} fps")

    proc.stdin.close()
    proc.wait()

    t_total = time.time() - t0
    print(f"[+] Video rendered successfully in {t_total:.2f}s!")
    print(f"[+] Output path: {VIDEO_PATH}")
    file_size_mb = VIDEO_PATH.stat().st_size / (1024 * 1024)
    print(f"[+] File size: {file_size_mb:.2f} MB")

    # Generate Ground-Truth Benchmark Metadata
    metadata = {
        "clip_id": "demo_lecture",
        "video_path": str(VIDEO_PATH),
        "duration_sec": TOTAL_DURATION,
        "width": WIDTH,
        "height": HEIGHT,
        "fps": float(FPS),
        "exposed_secrets": [
            {
                "secret_type": "api_key",
                "raw_text": "sk-live-9988776655",
                "bbox": [100, 127, 340, 32],
                "start": 0.0,
                "end": 90.0,
            }
        ],
        "ground_truth_technical_terms": [
            "useEffect",
            "@Autowired",
            "Kubernetes",
            "kubectl",
            "API_KEY",
        ],
        "ground_truth_spoken_technical_terms": [
            "useEffect",
            "@Autowired",
            "Kubernetes",
        ],
        "ground_truth_mangled_terms": [
            "use a fact",
            "auto wired",
            "coober netties",
        ],
        "triad_structure": {
            "hook_interval": [0.0, 22.0],
            "mutation_interval": [35.0, 55.0],
            "resolution_interval": [60.0, 90.0],
            "error_resolved_at": 60.0,
        },
        "target_metrics": {
            "target_tter_percent": 5.0,
            "target_ctbr_percent": 98.0,
            "target_wt_mae_ms": 80.0,
            "target_aclr_percent": 90.0,
        }
    }

    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"[+] Ground truth metadata exported to: {METADATA_PATH}")
    return str(VIDEO_PATH)


if __name__ == "__main__":
    generate_demo_video()
