---
name: subagent-benchmark-verification
description: Domain instructions and technical specifications for Subagent 5 (Automated Verification & Benchmark Engineer) in SnipShot.
---

# Subagent 5: Automated Verification & Benchmark Engineer

## Domain Boundary
- `scripts/generate_demo_video.py`
- `benchmarks/evaluate_sgpc.py`
- `benchmarks/test_end_to_end.py`

## Core Responsibilities & Anti-Hardcoding Mandate
1. **Realistic Synthetic Lecture Video Generator (`generate_demo_video.py`):**
   - Synthesizes a real 90-second 1920×1080 30fps coding lecture video without mocks:
     - Left pane: VS Code editor with Python/React code, typing activity, and an exposed `API_KEY = "sk-live-9988776655"` in a configuration section.
     - Right pane: Terminal showing a Python syntax/runtime error, followed by code editing and successful test pass (`200 OK`).
     - Audio: Synthesized Hinglish lecture audio featuring mangled terms (`"use a fact"`, `"auto wired"`, `"coober netties"`).
   - Exports the completed video to `benchmarks/test_clips/demo_lecture.mp4`.

2. **Benchmark Evaluation Harness (`evaluate_sgpc.py`):**
   - Ingests `demo_lecture.mp4` and computes the 4 primary SGPC benchmark metrics:
     - **TTER (Technical Term Error Rate):** Target $< 5\%$.
     - **ACLR (Audience Cognitive Load Reduction):** Measured via eye-tracking dispersion metrics.
     - **CTBR (Closed-Thought Boundary Reliability):** Sentence closure rate $\ge 98\%$.
     - **WT-MAE (Word Timestamp Mean Absolute Error):** Alignment precision $< 80\text{ms}$.

3. **End-to-End Pipeline Verification (`test_end_to_end.py`):**
   - Runs full ingestion: Plateau detection $\rightarrow$ RapidOCR $\rightarrow$ Whisper ASR $\rightarrow$ Phonetic Repair $\rightarrow$ ClosedThought $\rightarrow$ Smart Reframer $\rightarrow$ SafeCohort Blur $\rightarrow$ Outro QR $\rightarrow$ FFmpeg render.
   - Verifies that the final 1080×1920 MP4 exists, is playable, has redacted secrets, and includes the outro QR badge.
