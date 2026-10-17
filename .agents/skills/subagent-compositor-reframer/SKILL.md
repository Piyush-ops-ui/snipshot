---
name: subagent-compositor-reframer
description: Domain instructions and technical specifications for Subagent 3 (9:16 Smart Reframer & Fast Compositor Engineer) in SnipShot.
---

# Subagent 3: 9:16 Smart Reframer & Fast Compositor Engineer

## Domain Boundary
- `backend/app/core/smart_reframer.py`
- `backend/app/core/compositor.py`
- `backend/app/services/ffmpeg_service.py`

## Core Responsibilities & Anti-Hardcoding Mandate
1. **Weapon 2 (`SplitStage` & `Readable916` 3-Mode Reframer):**
   - Analyzes spatial bounding boxes of typing and cursor activity on the 16:9 source frame.
   - Mode 1 (*Single-Focus*): 65% inner dead-zone L1-smoothed camera path that eliminates jitter while tracking active code lines.
   - Mode 2 (*Dual-ROI SplitStage*): When simultaneous Left-IDE and Right-Terminal/Diagram activity is detected, crops both regions and stacks them vertically into a 1080×1020 upper viewport and a 1080×680 lower viewport.
   - Mode 3 (*AST Code Spotlight*): Whenever source lines exceed 850px width, triggers a crisp 32px monospace syntax card so 0 characters are cut off on mobile screens.

2. **Weapon 5 Execution (`SafeCohort` Localized Blur):**
   - Applies `cv2.GaussianBlur(roi, (51, 51), 0)` directly onto the source frame over all active `RedactionBox` coordinates prior to cropping and compositing.

3. **Weapon 7 (4 Pedagogical Archetype Templates):**
   - `standard_spotlight`: Clean branded layout with high-contrast karaoke word HUD.
   - `bug_hunter`: Header bar dynamically shifts from Crimson Red (`#7F1D1D`) during error state to Emerald Green (`#064E3B`, `BUG RESOLVED [200 OK]`) at the `error_resolved_at` timestamp.
   - `vs_battle`: Renders dual card comparison (`❌ Legacy / Verbose` vs `✅ Modern / Optimal`).
   - `predict_output`: Inserts a 2-second freeze-frame callout banner (`⏸️ PAUSE & COMMENT OUTPUT!`) before terminal verification.

4. **Weapon 8 Execution (Outro QR Code Bumper):**
   - Generates an offline 360×360 QR badge using Python `qrcode` in the 2-second outro bumper, encoding the exact code snippet for viewers to scan and copy.

5. **Weapon 9 (Dead-Air 2.5x Typing Hyperlapse):**
   - Detects silent typing intervals $>1.2\text{s}$ between spoken words and accelerates playback by 2.5x during those intervals, displaying a glowing `⚡ 2.5x HYPERLAPSE` HUD badge.

6. **Fast Streaming FFmpeg Subprocess Pipe:**
   - Detects Intel Arc hardware video encoding (`-c:v h264_qsv -global_quality 21`) using `/dev/dri/renderD128`, falling back to `-c:v libx264 -preset ultrafast -crf 21`.
   - Streams raw RGBA frames directly into FFmpeg stdin with zero intermediate disk frame writes for sub-15s 1080×1920 30fps renders.
