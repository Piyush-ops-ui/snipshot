---
name: subagent-pedagogical-brain
description: Domain instructions and technical specifications for Subagent 2 (Pedagogical Brain & Mode B Compiler Engineer) in SnipShot.
---

# Subagent 2: Pedagogical Brain & Mode B Compiler Engineer

## Domain Boundary
- `backend/app/core/closed_thought.py`
- `backend/app/core/mode_b_compiler.py`
- `backend/app/core/tree_sitter_gate.py`
- `backend/app/core/feedback_bandit.py`

## Core Responsibilities & Anti-Hardcoding Mandate
1. **Weapon 3 (`ClosedThought` Highlight Scorer):**
   - Ingests real audio waveforms and calculates RMS vocal energy across temporal frames.
   - Computes visual typing diff density and technical term frequency from TSSG nodes.
   - Evaluates the Pedagogical Triad:
     $$S_{\text{triad}} = w_1 \cdot \text{RMS}_{\text{audio}} + w_2 \cdot \text{Diff}_{\text{visual}} + w_3 \cdot \text{Tech}_{\text{density}} + w_4 \cdot \text{Bug2Fix}_{\text{bonus}} - w_5 \cdot \text{Penalty}_{\text{deictic}}$$
   - Detects dangling deictic pronouns (*"isko"*, *"ye wala"*, *"this"*, *"therefore"*) in the first 3 seconds of a clip and applies a heavy score penalty.
   - Magnetically snaps clip start and end boundaries to sentence ends and natural audio pauses ($\ge 0.4\text{s}$) strictly within the 30s–60s duration window.

2. **Mode B (`VerifiedCodeReel` Topic Explainer Compiler):**
   - Queries local Ollama (`qwen2.5-coder:3b-instruct-q4_K_M`) or Google Gemini Flash API fallback.
   - Emits 4 structured pedagogical beats: (1) Hook, (2) Core Concept Code, (3) Contrast/Mutation, (4) Terminal Verification.
   - Validates all code blocks using `tree-sitter` (guaranteeing 0 syntax errors, max 14 lines, max 42 characters per line).
   - Generates neural speech per beat using `edge-tts` (`en-IN-NeerjaNeural`) or offline `kokoro-onnx` and locks character typing animation duration to audio length (0ms drift).

3. **Weapon 8 (AST-Grounded Social Growth Pack):**
   - Synthesizes 3-tiered hashtags: Broad (`#coding #webdev`), Stack (`#react #javascript`), Micro-API (`#useEffect #useState`).
   - Generates curiosity-inducing hook title, pinned code snippet comment, and code string for the outro QR code.

4. **Weapon 6 (`PedagogyScore` Contextual Bandit Loop):**
   - Maintains an SQLite database (`data/db/snipshot.db`) storing feature vectors and viewer engagement telemetry.
   - Performs online LinUCB / Bayesian weight updates ($w_1..w_5$) so highlight scoring continuously improves.
