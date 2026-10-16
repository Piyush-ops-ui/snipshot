# SnipShot (Reel Studio): Architectural Foundation & Technical Plan

**Document Version:** 1.0.0  
**Status:** Approved Architectural Blueprint  
**System Classification:** Local-First Multimodal Pedagogical Video Studio (`SGPC`)  

---

## 1. Executive Summary & Architectural Vision

**SnipShot (Reel Studio)** is a local-first, production-grade video compilation platform designed to solve **Cross-Modal Pedagogical Desynchronisation** in technical education. Existing automated clipping tools fail catastrophically on programming and technical lectures because they treat speech recognition, video cropping, and clip selection as independent, unimodal tasks:

1. **Audio ASR fails on Hinglish and technical identifiers** (`useEffect`, `@Autowired`, `kubectl`) because the acoustic model cannot inspect the instructor's screen.
2. **Naive 9:16 centre-cropping causes geometric truncation**, cutting wide horizontal code lines in half or scaling code down below human readability thresholds.
3. **Engagement-based clippers select fragmented snippets**, clipping mid-clause on vocal spikes and creating clips with unresolved deictic pronouns (*"isko yahan pass karenge"*).

SnipShot implements **Screen-Grounded Pedagogical Compilation (SGPC)**, an architecture powered by a unified intermediate representation—the **Time-Aligned Screen-Speech Graph (TSSG)**—and standardized through **`Reel-IR`**. Both recorded 16:9 lectures (**Mode A: Decompilation**) and synthetic topic prompts (**Mode B: Compilation**) compile into the exact same editable 5-track `Reel-IR` timeline, rendered deterministically through a zero-bloat `Pillow + Pygments + FFmpeg` streaming pipeline.

```
+---------------------------------------------------------------------------------------------------+
|                                       INPUT MODES                                                 |
|   [Mode A: 16:9 Lecture Video (Screen + Audio)]         [Mode B: Topic Prompt (e.g. 'JSON vs XML')]|
+------------------------------------+-------------------------------------+------------------------+
                                     |                                     |
                                     v                                     v
                 +-----------------------------------+     +-----------------------------------+
                 | Mode A: Screen-Grounded Decompiler|     | Mode B: AST Pedagogical Compiler  |
                 | - Sparse Plateau Video OCR        |     | - Beat-Structured Script Gen      |
                 | - ScreenLex Biased Hinglish ASR   |     | - Tree-Sitter 42-Char Syntax Gate |
                 | - ClosedThought Triad Clipper     |     | - Local Neural TTS + Audio Sync   |
                 | - SplitStage + Readable916 Reframer|    +-----------------+-----------------+
                 +-----------------+-----------------+                       |
                                   |                                         |
                                   +-------------------+---------------------+
                                                       |
                                                       v
                               +-----------------------------------------------+
                               |           UNIFIED Reel-IR SCHEMA              |
                               |  - Word Timestamps & Prov Badges              |
                               |  - Multi-Viewport Keyframes (SplitStage)      |
                               |  - Mobile Code Cards (Readable916)            |
                               |  - Brand Kit Configuration                    |
                               +-----------------------+-----------------------+
                                                       |
                                                       v
                               +-----------------------------------------------+
                               |         INTERACTIVE STUDIO & ENGINE           |
                               |  - React + TypeScript + WaveSurfer Editor     |
                               |  - Sentence-Snap Handles & Provenance Modal   |
                               |  - Deterministic Pillow + FFmpeg Compositor   |
                               |  - Hardware Auto-Profiler (0-OOM Guarantee)   |
                               +-----------------------+-----------------------+
                                                       |
                                                       v
                               +-----------------------------------------------+
                               | OUTPUT: 1080x1920 9:16 Branded Pedagogical MP4 |
                               +-----------------------------------------------+
```

---

## 2. Core Architectural Pillars

### Pillar 1: Visual-Lexical Screen-Grounded ASR (`ScreenLex-ASR`)
- **Mechanism:** Samples the video at 2 FPS in low resolution to detect *visual plateaus* (moments where screen content stabilizes after typing or scrolling). Stabilized frames are processed with high-resolution `RapidOCR` to extract technical tokens (camelCase, snake_case, decorators `@Autowired`, CLI flags, and package names).
- **Two-Pass Biasing & Repair:**
  - *Pass 1 (Lexicon Seeding):* The top 60 screen identifiers populate `faster-whisper`'s `hotwords` and Romanized Hinglish `initial_prompt`.
  - *Pass 2 (Phonetic-Surface Alignment):* Spoken words with low confidence or high phonetic similarity are matched against on-screen tokens via a combined metric:
    $$\text{Sim}(w, c) = 0.55 \cdot \text{JaroWinkler}(\text{Metaphone}(w), \text{Metaphone}(c)) + 0.45 \cdot \text{NormalizedLevenshtein}(\text{norm}(w), \text{norm}(c)) + \text{ScreenBonus}$$
  - Multi-syllable phrases like `"use a fact"` or `"cube control"` are automatically merged into single tokens (`useEffect`, `kubectl`) with exact millisecond start/end timestamps and visual bounding-box provenance.

### Pillar 2: Adaptive 9:16 Viewport Retargeting (`SplitStage` + `Readable916`)
- **Mechanism:** Solves the 9:16 geometric paradox without naive centre cropping or nauseating cursor tracking.
- **Three-Mode Retargeter:**
  1. *Mode 1 (Damped Single Focus):* When code activity is compact ($w_{\text{roi}} \le 850\text{px}$), an L1-regularized dead-zone camera filter maintains a stationary hold inside a 65% dead-zone, transitioning only with smooth Hermite splines ($>0.5\text{s}$) or instant cuts when focus shifts across panels.
  2. *Mode 2 (Dual-ROI `SplitStage`):* When activity co-occurs across horizontal panes (e.g., Left IDE editor + Right Terminal execution/browser), the frame is split and restacked vertically into an upper $1080 \times 1020\text{px}$ editor crop and lower $1080 \times 680\text{px}$ terminal crop.
  3. *Mode 3 (`Readable916` Code Spotlight Card):* When active code exceeds 850px in width, the system lifts the active 6–12 lines via OCR and AST parsing into an overlay card with 32px monospace typography, syntax highlighting, and line wrapping, guaranteeing zero horizontal character truncation.

### Pillar 3: Pedagogical Triad & Deictic Closure Highlights (`ClosedThought`)
- **Mechanism:** Clips are extracted not on acoustic volume spikes, but on complete pedagogical state transitions.
- **Scoring Function:**
  $$\text{Score}(i, j) = w_1 \cdot \text{Prosody}(i,j) + w_2 \cdot \text{VisualChange}(i,j) + w_3 \cdot \text{TechDensity}(i,j) + w_4 \cdot \text{TriadClosure}(i,j) - w_5 \cdot \text{DeicticPenalty}(u_i)$$
- **Boundary Snapping:** Clips are strictly snapped to complete grammatical sentence boundaries. A $+2.0$ penalty suppresses candidate clips starting with unresolved deictic pronouns (*"isko yahan..."*, *"and this variable..."*) before the referent is introduced. A triad bonus ($+1.5$) rewards clips with an introductory hook, a code mutation, and a terminal verification or summary discourse marker.

### Pillar 4: Unified `Reel-IR` Intermediate Representation
- **Mechanism:** Decompiled lecture segments (Mode A) and prompt-synthesized explainers (Mode B) share a single declarative schema.
- **Composition Engine:** A lightweight Python streaming worker generates frame overlays with `Pillow` and `Pygments` and pipes raw image frames directly into an `FFmpeg` subprocess. This eliminates heavy browser engines (Puppeteer/Remotion) and achieves sub-10s rendering times on local CPUs.

---

## 3. Production Directory Structure

The repository follows a clean, decoupled monorepo layout:

```text
snipshot/
├── plan.md                                # Comprehensive architectural foundation (this document)
├── workflow.md                            # Visual operational workflows (Mermaid.js diagrams)
├── research.md                            # Foundational research, competitor audits, and literature
├── README.md                              # Project overview, installation instructions, quickstart
├── package.json                           # Root scripts and workspace management
├── docker-compose.yml                     # Optional containerized local deployment
│
├── backend/                               # Python 3.11+ FastAPI Core Engine
│   ├── pyproject.toml                     # Poetry/pip build configuration and dependency locks
│   ├── requirements.txt                   # Production Python dependencies
│   ├── requirements-dev.txt               # Testing and linting dependencies
│   ├── .env.example                       # Template for local environment variables
│   │
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                        # FastAPI entrypoint, CORS, routers, lifecycle hooks
│   │   ├── config.py                      # Pydantic BaseSettings (paths, models, timeouts)
│   │   │
│   │   ├── api/                           # REST & Streaming Endpoints
│   │   │   ├── __init__.py
│   │   │   ├── router.py                  # API router aggregation
│   │   │   ├── endpoints/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── lecture.py             # Mode A: Upload, analyze, plateau, extract highlights
│   │   │   │   ├── explainer.py           # Mode B: Prompt-to-explainer script & audio generation
│   │   │   │   ├── timeline.py            # Reel-IR CRUD, boundary adjustment, token overrides
│   │   │   │   ├── render.py              # Video composition, export job trigger, progress SSE
│   │   │   │   ├── brands.py              # Brand kit management (logos, fonts, palettes)
│   │   │   │   └── benchmark.py           # Evaluation runner, metrics query, telemetry import
│   │   │   └── websockets/
│   │   │       ├── __init__.py
│   │   │       └── progress.py            # Real-time processing & rendering progress websocket
│   │   │
│   │   ├── core/                          # Core Algorithmic Engines
│   │   │   ├── __init__.py
│   │   │   ├── plateau_detector.py        # 2 FPS greyscale absdiff, stable frame extraction
│   │   │   ├── screen_lex_ocr.py          # RapidOCR runner, bbox clustering, identifier regex filter
│   │   │   ├── grounded_asr.py            # faster-whisper + stable-ts + Romanized Hinglish seed
│   │   │   ├── phonetic_repair.py         # Metaphone + Levenshtein + token merger + bbox provenance
│   │   │   ├── tssg_builder.py            # Time-Aligned Screen-Speech Graph node/edge constructor
│   │   │   ├── closed_thought.py          # Multimodal Triad, deictic penalizer, Bug2Fix detector
│   │   │   ├── smart_reframer.py          # 3-Mode selector: Dead-Zone L1, SplitStage, Readable916
│   │   │   ├── mode_b_compiler.py         # Beat-structured prompt compiler + Tree-sitter gate
│   │   │   ├── tree_sitter_gate.py        # CST parser, syntax validator, 42-char line-width guard
│   │   │   ├── tts_engine.py              # Kokoro-82M / Piper local TTS + millisecond bookmark sync
│   │   │   ├── compositor.py              # Pillow/Pygments HUD synthesizer + FFmpeg streaming pipe
│   │   │   └── feedback_bandit.py         # Contextual bandit weight updater (PedagogyScore)
│   │   │
│   │   ├── schemas/                       # Canonical Data Contracts & Pydantic Models
│   │   │   ├── __init__.py
│   │   │   ├── reel_ir.py                 # Unified Reel-IR schema (Mode A & Mode B)
│   │   │   ├── tssg.py                    # Time-Aligned Screen-Speech Graph schema
│   │   │   ├── brand.py                   # BrandKit schema (colors, fonts, watermarks, bumpers)
│   │   │   ├── benchmark.py               # Evaluation metrics (TTER, ACLR, CTBR, WT-MAE)
│   │   │   └── api_requests.py            # Endpoint request & response envelopes
│   │   │
│   │   ├── services/                      # Infrastructure & Hardware Abstraction
│   │   │   ├── __init__.py
│   │   │   ├── hardware_profiler.py       # Auto-detects CPU/RAM/VRAM and sets Tier 1/2/3 profile
│   │   │   ├── memory_manager.py          # Sequential model unloader & gc collector (0-OOM)
│   │   │   ├── cache_service.py           # Disk-backed SHA-256 hash cache for instant reloads
│   │   │   └── ffmpeg_service.py          # Subprocess wrappers, probe utils, filtergraph builders
│   │   │
│   │   └── data/                          # Bundled Lexicons & Default Assets
│   │       ├── tech_glossary.json         # 2,000+ curated CS terms, libraries, CLI tools
│   │       ├── hinglish_patterns.json     # Romanized Hinglish stopwords and deictic markers
│   │       ├── default_brand_kits.json    # Pre-configured templates (Dark, Light, Brand)
│   │       └── fonts/                     # Bundled open-source fonts (JetBrains Mono, Inter)
│   │           ├── JetBrainsMono-Bold.ttf
│   │           └── Inter-SemiBold.ttf
│   │
│   └── tests/                             # Backend Test Suite
│       ├── conftest.py                    # Pytest fixtures, mock video frames, mock transcripts
│       ├── test_plateau_detector.py       # Unit tests for visual change detection
│       ├── test_phonetic_repair.py        # Unit tests for Hinglish identifier repair
│       ├── test_smart_reframer.py         # Tests for dead-zone hysteresis & SplitStage layout
│       ├── test_tree_sitter_gate.py       # Tests for code syntax and line-width enforcement
│       ├── test_compositor.py             # Integration tests for FFmpeg frame rendering
│       └── test_reel_ir_validation.py     # Schema compliance tests
│
├── frontend/                              # Modern React + Vite + TypeScript Studio
│   ├── package.json                       # Frontend dependencies (React, Vite, WaveSurfer, Lucide)
│   ├── tsconfig.json                      # Strict TypeScript compiler options
│   ├── vite.config.ts                     # Vite build configuration and API proxy
│   ├── tailwind.config.js                 # Tailwind CSS styling tokens
│   ├── index.html                         # Single-page application root
│   │
│   ├── src/
│   │   ├── main.tsx                       # React DOM mount point
│   │   ├── App.tsx                        # Studio shell: mode selector, layout container
│   │   ├── index.css                      # Global styles, font definitions, custom scrollbars
│   │   │
│   │   ├── components/                    # Studio UI Components
│   │   │   ├── common/
│   │   │   │   ├── Header.tsx             # Studio navigation, mode toggle, export button
│   │   │   │   ├── Badge.tsx              # Provenance & metric status badges
│   │   │   │   ├── Modal.tsx              # Accessible dialog overlay
│   │   │   │   └── Tabs.tsx               # Accessible tab switcher
│   │   │   ├── timeline/
│   │   │   │   ├── TimelineEditor.tsx     # WaveSurfer waveform + draggable sentence-snap handles
│   │   │   │   ├── TranscriptTrack.tsx    # Interactive word-by-word karaoke transcript
│   │   │   │   └── ViewportTrack.tsx      # Visual keyframe track (Single Focus vs SplitStage)
│   │   │   ├── player/
│   │   │   │   ├── VideoPreview.tsx       # 9:16 Canvas player with overlays
│   │   │   │   └── ComparisonPlayer.tsx   # Side-by-side Naive Centre Crop vs. SGPC 9:16
│   │   │   ├── provenance/
│   │   │   │   └── ProvenanceInspector.tsx # Visual proof modal (raw ASR vs OCR frame crop)
│   │   │   ├── brand/
│   │   │   │   └── BrandKitDrawer.tsx     # Real-time colors, fonts, logos, intro/outro editor
│   │   │   ├── explainer/
│   │   │   │   ├── ModeBStudio.tsx        # Topic prompt editor, syntax gate badge, beat viewer
│   │   │   │   └── BeatCard.tsx           # Individual code-diff + audio sync beat editor
│   │   │   └── benchmark/
│   │   │       └── BenchmarkDrawer.tsx    # Live TTER, ACLR, CTBR evaluation metrics panel
│   │   │
│   │   ├── hooks/                         # Custom React Hooks
│   │   │   ├── useReelIR.ts               # Reel-IR state management, undo/redo, autosave
│   │   │   ├── useWaveSurfer.ts           # Audio waveform initialization and zoom control
│   │   │   ├── useProgressSocket.ts       # WebSocket/SSE connection for render progress
│   │   │   └── useHardwareProfile.ts      # Hardware tier state and recommendation banner
│   │   │
│   │   ├── types/                         # TypeScript Type Mirrors
│   │   │   ├── reel_ir.ts                 # Full TypeScript mirror of backend Reel-IR schema
│   │   │   ├── brand.ts                   # BrandKit TypeScript types
│   │   │   └── api.ts                     # API payload interfaces
│   │   │
│   │   └── services/                      # Frontend API Clients
│   │       └── api.ts                     # Axios/fetch wrappers for all backend endpoints
│   │
│   └── public/                            # Static Frontend Assets
│       ├── favicon.ico
│       └── logo.svg                       # SnipShot official branding icon
│
├── benchmarks/                            # Automated Evaluation Harness
│   ├── evaluate_sgpc.py                   # Full automated benchmark runner (TTER, ACLR, CTBR)
│   ├── synthetic_dataset_generator.py     # Generates mock Hinglish audio and IDE test frames
│   ├── test_clips/                        # Benchmark test clips metadata and ground truth
│   │   ├── clip1_react_hinglish.json      # Ground-truth tokens: useEffect, useState, cleanup
│   │   ├── clip2_spring_split.json        # Ground-truth tokens: @Autowired, terminal split
│   │   ├── clip3_k8s_diagram.json         # Ground-truth tokens: kubectl, ingress, YAML
│   │   ├── clip4_fastapi_bug2fix.json     # Ground-truth tokens: KeyError, 500 error resolved
│   │   └── clip5_mode_b_prompts.json      # Mode B verification test suite
│   └── results/                           # Benchmark execution outputs & ablation logs
│       └── latest_benchmark_run.json
│
├── data/                                  # Runtime Storage & Persistent Cache
│   ├── uploads/                           # Ingested raw 16:9 MP4 lecture recordings
│   ├── cache/                             # Pre-computed OCR indices, audio WAVs, transcripts
│   ├── exports/                           # Rendered 1080x1920 9:16 MP4 video outputs
│   └── db/                                # SQLite database for local history and telemetry
│       └── snipshot.db
│
└── docs/                                  # Project Documentation
    ├── architecture.md                    # Detailed architecture notes
    └── api_reference.md                   # Complete OpenAPI specification
```

---

## 4. Canonical Data Contracts (`Reel-IR` & `TSSG`)

To ensure clean isolation between modules and prevent serialization bugs, all data exchanged across backend components and the frontend Studio uses strict Pydantic models mirrored in TypeScript interfaces.

### A. The Unified `Reel-IR` Schema (`backend/app/schemas/reel_ir.py`)

```python
from enum import Enum
from typing import List, Optional, Tuple
from pydantic import BaseModel, Field

class LayoutMode(str, Enum):
    SINGLE_FOCUS = "single_focus"      # Stabilized dead-zone camera on active region
    SPLIT_STAGE = "split_stage"        # Upper IDE crop + Lower Terminal/Diagram crop
    CODE_SPOTLIGHT = "code_spotlight"  # Rendered AST syntax card + zoomed context

class WordAlignment(BaseModel):
    id: str = Field(..., description="Unique word identifier")
    word: str = Field(..., description="Displayed word text")
    start: float = Field(..., description="Start timestamp in seconds")
    end: float = Field(..., description="End timestamp in seconds")
    confidence: float = Field(..., ge=0.0, le=1.0)
    is_technical: bool = Field(default=False)
    raw_asr_word: Optional[str] = Field(None, description="Original ungrounded word from ASR")
    provenance_frame_time: Optional[float] = Field(None, description="Timestamp of OCR frame source")
    provenance_bbox: Optional[Tuple[int, int, int, int]] = Field(None, description="[x, y, w, h] on source frame")
    provenance_thumbnail_url: Optional[str] = Field(None, description="URL/path to cropped pixel proof")

class ViewportKeyframe(BaseModel):
    timestamp: float = Field(..., description="Keyframe timestamp in seconds")
    mode: LayoutMode
    # Coordinates normalized to [0.0, 1.0] relative to 1920x1080 source
    top_crop: Tuple[float, float, float, float] = Field(..., description="[x, y, w, h] for upper viewport")
    bottom_crop: Optional[Tuple[float, float, float, float]] = Field(None, description="[x, y, w, h] for lower viewport (SplitStage)")
    transition_duration: float = Field(default=0.0, description="Duration in seconds (0.0 = instant jump-cut)")

class CodeSpotlightCard(BaseModel):
    id: str
    start: float
    end: float
    language: str = Field(default="python")
    code: str = Field(..., description="Syntax-formatted code snippet")
    active_line_indices: List[int] = Field(default_factory=list)
    verified_by_ast: bool = Field(default=True)

class BrandKitConfig(BaseModel):
    id: str = "default_dark"
    name: str = "Default Dark Studio"
    primary_color: str = "#00F2FE"       # Cyan accent for technical terms & progress
    secondary_color: str = "#4FACFE"     # Secondary gradient tone
    background_color: str = "#0F172A"    # Deep slate background
    text_color: str = "#F8FAFC"          # Monospace high-contrast white
    font_family: str = "JetBrains Mono"
    font_size_pt: int = 32
    logo_path: Optional[str] = None
    logo_position: str = "top_right"     # "top_left", "top_right", "bottom_left"
    show_provenance_badge: bool = True
    enable_intro_bumper: bool = False
    intro_bumper_duration: float = 1.5
    enable_outro_bumper: bool = True
    outro_bumper_duration: float = 2.0
    watermark_text: Optional[str] = "TechSummitTrainers"

class ReelIR(BaseModel):
    schema_version: str = "1.0.0"
    reel_id: str
    mode: str = Field(..., description="'mode_a_extract' or 'mode_b_prompt'")
    title: str
    source_media_path: Optional[str] = None
    clip_start: float = Field(..., description="Start timestamp within source video")
    clip_end: float = Field(..., description="End timestamp within source video")
    total_duration: float = Field(..., description="Duration in seconds (clip_end - clip_start)")
    
    # 5-Track Declarative Timeline
    audio_path: str = Field(..., description="Path to extracted or synthesized audio WAV")
    transcript: List[WordAlignment] = Field(..., description="Word-level aligned transcript track")
    viewports: List[ViewportKeyframe] = Field(..., description="Viewport retargeting track")
    code_cards: List[CodeSpotlightCard] = Field(default_factory=list, description="Readable916 overlay track")
    brand_kit: BrandKitConfig = Field(default_factory=BrandKitConfig)
    
    # Pedagogical Metadata & Provenance
    pedagogical_score: float = Field(default=0.0, description="Overall Pedagogical Triad Score")
    entry_closure_verified: bool = Field(default=True)
    exit_closure_verified: bool = Field(default=True)
    technical_term_count: int = Field(default=0)
    created_at: str
```

### B. TypeScript Equivalent (`frontend/src/types/reel_ir.ts`)

```typescript
export type LayoutMode = 'single_focus' | 'split_stage' | 'code_spotlight';

export interface WordAlignment {
  id: string;
  word: string;
  start: number;
  end: number;
  confidence: number;
  is_technical: boolean;
  raw_asr_word?: string;
  provenance_frame_time?: number;
  provenance_bbox?: [number, number, number, number];
  provenance_thumbnail_url?: string;
}

export interface ViewportKeyframe {
  timestamp: number;
  mode: LayoutMode;
  top_crop: [number, number, number, number];
  bottom_crop?: [number, number, number, number];
  transition_duration: number;
}

export interface CodeSpotlightCard {
  id: string;
  start: number;
  end: number;
  language: string;
  code: string;
  active_line_indices: number[];
  verified_by_ast: boolean;
}

export interface BrandKitConfig {
  id: string;
  name: string;
  primary_color: string;
  secondary_color: string;
  background_color: string;
  text_color: string;
  font_family: string;
  font_size_pt: number;
  logo_path?: string;
  logo_position: 'top_left' | 'top_right' | 'bottom_left';
  show_provenance_badge: boolean;
  enable_intro_bumper: boolean;
  intro_bumper_duration: number;
  enable_outro_bumper: boolean;
  outro_bumper_duration: number;
  watermark_text?: string;
}

export interface ReelIR {
  schema_version: string;
  reel_id: string;
  mode: 'mode_a_extract' | 'mode_b_prompt';
  title: string;
  source_media_path?: string;
  clip_start: number;
  clip_end: number;
  total_duration: number;
  audio_path: string;
  transcript: WordAlignment[];
  viewports: ViewportKeyframe[];
  code_cards: CodeSpotlightCard[];
  brand_kit: BrandKitConfig;
  pedagogical_score: number;
  entry_closure_verified: boolean;
  exit_closure_verified: boolean;
  technical_term_count: number;
  created_at: string;
}
```

---

## 5. Core Modules & Component Responsibilities

### 1. `backend/app/core/plateau_detector.py`
- **Responsibility:** Ingests raw video at 2 FPS in 480×270 grayscale to detect *visual plateaus* (stable intervals where screen changes have completed, e.g., typing pauses or IDE output holds).
- **Core Methods:**
  - `detect_plateaus(video_path: str, change_threshold: float = 0.04, min_hold_duration: float = 0.8) -> List[PlateauFrame]`
  - Computes normalized mean absolute pixel difference: $d_t = \frac{1}{N}\sum |I_t - I_{t-1}|$.
  - Extracts full-resolution 1080p frames only when $d_t > \theta_{\text{change}}$ is followed by $d_{t+1} < \theta_{\text{stable}}$.
- **Output:** A list of stabilized keyframe timestamps and 1080p frame image files.

### 2. `backend/app/core/screen_lex_ocr.py`
- **Responsibility:** Runs high-accuracy, low-latency ONNX-based OCR on plateau frames, extracts bounding boxes, and filters programming identifiers.
- **Core Methods:**
  - `extract_screen_tokens(plateau_frames: List[PlateauFrame]) -> List[ScreenToken]`
  - Applies a CLAHE contrast enhancement pre-filter to handle dark-mode IDE editors cleanly.
  - Executes `RapidOCR` to extract text lines and bounding boxes `[x, y, w, h]`.
  - Filters tokens using strict technical regexes: camelCase (`[a-z]+[A-Z][a-zA-Z0-9]*`), decorators (`@[A-Za-z]+`), snake_case, CLI commands, and intersections with `tech_glossary.json`.
- **Output:** A temporal index of screen identifiers with pixel coordinates: $\mathcal{L}(t)$.

### 3. `backend/app/core/grounded_asr.py` & `phonetic_repair.py`
- **Responsibility:** Executes speech recognition and word alignment on Hinglish audio, then repairs mistranscriptions using on-screen tokens.
- **Core Methods:**
  - `transcribe_with_bias(audio_path: str, screen_lexicon: List[ScreenToken]) -> List[ASRWord]`
    - Injects top screen tokens into `faster-whisper`'s `hotwords` argument.
    - Sets `initial_prompt = "Technical coding lecture in Romanized Hinglish and English. Key terms: " + top_tokens`.
    - Obtains DTW-stabilized word alignments via `stable-ts`.
  - `repair_technical_words(words: List[ASRWord], screen_lexicon: List[ScreenToken]) -> List[WordAlignment]`
    - Evaluates sliding windows of $k \in \{1, 2, 3\}$ words against candidates visible within $\pm 20$ seconds.
    - Computes phonetic Metaphone similarity and Jaro-Winkler string distance.
    - If score $\ge 0.82$, merges words into a single technical token (`grounded_word`), attaches the source bounding box `provenance_bbox`, and saves a cropped image thumbnail for the UI.
- **Output:** Fully aligned, phonetically repaired `WordAlignment` stream.

### 4. `backend/app/core/closed_thought.py`
- **Responsibility:** Scores candidate 30–60s spans to extract complete, pedagogically sound teaching moments.
- **Core Methods:**
  - `score_candidates(transcript: List[WordAlignment], audio_path: str, diff_timeline: List[float]) -> List[ScoredCandidate]`
  - Enforces the **Deictic Penalty**: penalizes spans that begin with dangling referents (*"isko"*, *"and then this"*).
  - Enforces the **Triad Bonus**: rewards spans containing an initial problem statement, middle code/diagram mutation, and terminal verification.
  - Automatically snaps boundaries backward/forward to the nearest complete grammatical sentence boundary.
- **Output:** Top-ranked candidate clip spans $[T_0, T_1]$ with metric breakdowns.

### 5. `backend/app/core/smart_reframer.py`
- **Responsibility:** Computes 9:16 viewport trajectories for a selected clip interval.
- **Core Methods:**
  - `compute_viewports(clip_start: float, clip_end: float, screen_tokens: List[ScreenToken], diff_maps: List[DiffRegion]) -> List[ViewportKeyframe]`
  - Classifies the scene into one of three modes:
    - *Single Focus:* Applies dead-zone hysteresis filter (65% stationary hold) on cursor/edit centroid.
    - *Dual-ROI SplitStage:* Detects active left-pane (IDE) and right-pane (Terminal/Output) bimodal activity and generates dual-crop keyframes.
    - *Code Spotlight:* Flags lines wider than 850px and triggers `tree_sitter_gate.py` to lift the block into a formatted `CodeSpotlightCard`.
- **Output:** The `viewports` and `code_cards` tracks of `Reel-IR`.

### 6. `backend/app/core/mode_b_compiler.py` & `tree_sitter_gate.py`
- **Responsibility:** Compiles a topic prompt (e.g., `"JSON vs XML"`) into a synchronized code explainer Reel.
- **Core Methods:**
  - `generate_beat_script(prompt: str, brand: BrandKitConfig) -> BeatScript`
    - Uses local `Qwen2.5-Coder-3B` (or configured API fallback) to produce a structured 4-beat explainer.
  - `validate_code_syntax(code: str, language: str) -> ASTValidationResult`
    - Runs `py-tree-sitter` to guarantee 0 syntax errors.
    - Enforces the **Mobile Legibility Constraint: max 42 characters per line, max 14 lines per card**.
  - `synthesize_narration(beats: List[Beat]) -> Tuple[str, List[WordAlignment]]`
    - Runs `Kokoro-82M` (ONNX) or `Piper` locally to generate audio for each beat, calculating exact millisecond durations to align typing animations with voiceover.
- **Output:** A valid `Reel-IR` document ready for the Studio preview and compositor.

### 7. `backend/app/core/compositor.py`
- **Responsibility:** Renders the declarative `Reel-IR` timeline into a high-definition 1080×1920 MP4 video.
- **Core Methods:**
  - `render_reel(reel: ReelIR, output_path: str, progress_callback: Callable[[float], None]) -> str`
  - Generates transparent HUD overlays in memory using `Pillow`:
    - Word-by-word karaoke captions with cyan active-word highlighting.
    - Glowing visual provenance badges for repaired technical terms.
    - High-contrast syntax-highlighted code cards (via `Pygments`).
    - Institute Brand Kit watermarks, logos, and header banners.
  - Pipes raw frames into an `FFmpeg` subprocess configured with hardware-accelerated video encoding (`h264_nvenc` or multi-threaded CPU `libx264`).
- **Performance Guarantee:** 45s Reel renders in 8–15 seconds on a modern multi-core CPU.

---

## 6. Technology Stack Rationale & Boundaries

### Selected Stack vs. Alternatives

| Subsystem | Chosen Technology | Evaluated Alternatives | Rationale & Why Alternatives Were Rejected |
| :--- | :--- | :--- | :--- |
| **Backend Framework** | **FastAPI (Python 3.11+)** | Django, Flask, Express.js | Native async support, automatic OpenAPI docs, tight integration with Python ML/CV libraries, high throughput. |
| **ASR Engine** | **`faster-whisper` + `stable-ts`** | OpenAI Whisper, WhisperX, Vosk | CTranslate2 delivers 4× speedup and `int8` quantization. `faster-whisper` supports dynamic `hotwords`. `stable-ts` uses DTW cross-attention, avoiding `wav2vec2` crashes on mixed Hinglish. |
| **Screen OCR** | **`RapidOCR` (ONNXRuntime CPU)** | Tesseract 5, EasyOCR, PaddleOCR | Runs in 80–180ms per frame on CPU without heavy PyTorch or PaddlePaddle runtimes. Delivers superior dark-theme IDE text extraction. |
| **Code Parsing** | **`py-tree-sitter` + `Pygments`** | Python `ast`, Regex only | Incremental, error-tolerant CST/AST parser supporting Python, Java, JS/TS, Go, C++, HTML/XML. Enforces strict syntax and line-length constraints. |
| **Video Rendering** | **`Pillow` + `NumPy` + `FFmpeg` pipe** | Remotion, MoviePy v1, Manim | MoviePy is slow and leaks memory on frame copies. Remotion introduces heavy Node.js/Chromium overhead. Direct `FFmpeg` pipes render 1080×1920 @ 30fps in 8–15s on CPU. |
| **Local TTS (Mode B)**| **`Kokoro-82M` (ONNX) / `Piper`** | Coqui XTTS-v2, Bark, ElevenLabs | Bark/XTTS are too slow on CPU. Kokoro runs 3×–8× faster than real-time on CPU with near-human instructional quality at zero API cost. |
| **Local LLM** | **`Qwen2.5-Coder-3B-Instruct` (GGUF)** | Llama-3.2-3B, Phi-3.5-mini | Unrivaled code generation, JSON compliance, and technical comprehension in the 3B parameter class. Fits easily into 2.2GB RAM. |
| **Frontend Studio** | **React 18 + Vite + TypeScript** | Next.js, Electron | Minimal boilerplate, instantaneous HMR, clean separation from Python backend, simple static production build. |
| **Audio Waveform** | **WaveSurfer.js** | Wavesurfer-react, custom canvas | Industry standard for sub-second audio scrubbing, zoomable waveforms, and sentence-boundary snap handles. |
| **Styling** | **Tailwind CSS + Lucide Icons** | MUI, Ant Design, Chakra UI | Zero runtime CSS overhead, modern dark-mode aesthetics, full layout flexibility for custom multi-track timelines. |

### Dependency Boundaries & Isolation

1. **AI/CV Engine Isolation:** All heavy computations (Whisper, RapidOCR, FFmpeg) reside exclusively within the Python backend. The frontend communicates solely via REST endpoints, Server-Sent Events (SSE), and WebSockets.
2. **Sequential Memory Management (0-OOM Guarantee):** On memory-constrained laptops (8GB–16GB RAM), models are loaded sequentially:
   - *Phase 1:* Sparse OCR is executed, then ONNX session memory is released.
   - *Phase 2:* `faster-whisper` runs transcription, then weights are unloaded via `del model; gc.collect()`.
   - *Phase 3:* LLM scoring or Mode B generation runs in isolated memory.
   - *Phase 4:* FFmpeg streaming render executes with a lean 400MB memory footprint.
   Whisper and LLM models never reside in RAM simultaneously on Tier 1 systems.

---

## 7. Verification Plan & Test Strategy

### Automated Test Matrix
1. **Unit Tests (`pytest backend/tests`):**
   - `test_plateau_detector.py`: Verifies that frame differencing correctly isolates stable typing intervals.
   - `test_phonetic_repair.py`: Feeds synthetic Hinglish ASR output (`"use a fact"`, `"auto wire"`) alongside screen tokens (`useEffect`, `@Autowired`) and asserts 100% correct phonetic replacement.
   - `test_smart_reframer.py`: Asserts that horizontal bimodal activity triggers `SplitStage` and wide code lines trigger `Readable916`.
   - `test_tree_sitter_gate.py`: Validates syntax verification and asserts that lines $>42$ characters are flagged for reflow.
   - `test_reel_ir_validation.py`: Verifies bi-directional JSON serialization and Pydantic validation.

2. **Benchmark Harness (`benchmarks/evaluate_sgpc.py`):**
   - Evaluates the 5-clip technical benchmark and outputs quantitative metrics:
     - **TTER (Technical Term Error Rate):** Target $\ge 40\%$ reduction vs. baseline.
     - **ACLR (Active Code Legibility Rate):** Target $\ge 90\%$ (0 characters clipped horizontally).
     - **CTBR (Complete-Thought Boundary Rate):** Target $\ge 90\%$ boundary closure precision.
     - **WT-MAE (Word Timestamp Mean Absolute Error):** Target $<120\text{ms}$.

3. **Frontend Verification:**
   - `npm run build`: Validates strict TypeScript compilation and asset bundling.
   - Visual inspection of the side-by-side player, waveform snapping handles, and provenance proof popovers.
