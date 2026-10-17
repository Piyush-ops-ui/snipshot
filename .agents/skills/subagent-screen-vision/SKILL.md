---
name: subagent-screen-vision
description: Domain instructions and technical specifications for Subagent 1 (Screen-Vision & Grounded ASR Engineer) in SnipShot.
---

# Subagent 1: Screen-Vision & Grounded ASR Engineer

## Domain Boundary
- `backend/app/core/plateau_detector.py`
- `backend/app/core/screen_lex_ocr.py`
- `backend/app/core/grounded_asr.py`
- `backend/app/core/phonetic_repair.py`

## Core Responsibilities & Anti-Hardcoding Mandate
1. **Real 2-FPS Plateau Detector (`plateau_detector.py`):**
   - Decodes actual video frames via OpenCV at 2 FPS downscaled to 480x270 grayscale.
   - Computes normalized frame difference $d_t = \frac{1}{N} \sum |I_t - I_{t-1}|$.
   - Identifies stationary plateaus ($d_t < 0.04$) lasting $\ge 1.0\text{s}$ and captures 1080p keyframes for OCR.

2. **Weapon 1 (`ScreenLex-ASR`) & Visual Proofs (`screen_lex_ocr.py`):**
   - Applies CLAHE contrast enhancement (`cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))`) for dark-mode IDE editors.
   - Runs `RapidOCR` ONNX models to extract bounding boxes `[x, y, w, h]`, text tokens, and confidence.
   - Saves cropped 1080p source video screenshots of detected technical identifiers to `data/cache/provenance/st_<id>.png` and encodes base64 thumbnail for instant UI display.
   - Feeds top 60 screen identifiers as dynamic hotwords and Romanized Hinglish prompt to `faster-whisper`.
   - Runs sliding-window (1-to-3 words) Double-Metaphone + Jaro-Winkler phonetic repair to correct mangled terms (`"use a fact"` $\rightarrow$ `useEffect`, `"ought to wire"` $\rightarrow$ `@Autowired`).

3. **Weapon 4 (`Bug2Fix` Error Detector):**
   - Inspects plateau frames and terminal text boxes for compiler/runtime errors:
     - Error keywords: `Traceback`, `Error:`, `Exception`, `Failed`, `500 Internal`, `SyntaxError`, `TypeError`.
     - Red HSV color cluster thresholding ($H \in [0, 10] \cup [170, 180]$, $S > 120$, $V > 120$) in terminal window bounds.
   - Detects the transition from error state to clean execution/test pass, tagging `is_bug_to_fix_arc = True` and recording the exact `error_resolved_at` timestamp.

4. **Weapon 5 (`SafeCohort` Secret Shield):**
   - Scans extracted OCR bounding boxes with regex and Shannon entropy ($H > 3.8$) to detect exposed `.env` secrets, OpenAI keys (`sk-`), AWS access keys (`AKIA`), passwords, and emails.
   - Generates `RedactionBox` coordinates with temporal validity intervals `[start, end]`.
