# SnipShot (Reel Studio): Operational Workflows & System Pipelines

**Document Version:** 1.0.0  
**Status:** Approved Operational Blueprint  
**Diagram Standard:** Mermaid.js (Compatible with GitHub Markdown & Antigravity Studio)  

---

## 1. Bird's-Eye Operational Workflow

This high-level flowchart illustrates the end-to-end lifecycle of media assets inside **SnipShot**, mapping the path from raw inputs (Mode A lecture recordings or Mode B topic prompts) through the processing engines, the unified `Reel-IR` bridge, the interactive Studio, and final video composition.

```mermaid
flowchart TD
    subgraph Inputs["1. Ingestion Layer"]
        InputA["Mode A: 16:9 Lecture Video (MP4)\n- Screen recording (IDE / Diagram / Terminal)\n- Spoken Hinglish / English Audio Track"]
        InputB["Mode B: Topic Prompt & Constraints\n- Educational Concept (e.g., 'JSON vs XML')\n- Target Duration & Institute Brand Kit"]
    end

    subgraph Engines["2. Analysis & Synthesis Engines"]
        direction TB
        subgraph ModeA_Proc["Mode A: Screen-Grounded Decompiler"]
            A1["Audio Prosody & VAD Analysis"]
            A2["Plateau Detector (2 FPS Greyscale Diff)"]
            A3["ScreenLex OCR Identifier Miner"]
            A4["Visual-Biased Hinglish ASR (faster-whisper)"]
            A5["Phonetic-Surface Alignment & Repair"]
            A6["ClosedThought Triad Highlight Scorer"]
            A7["Smart Reframer (Dead-Zone / SplitStage)"]
            A8["SafeCohort Secret & PII Scanner (API Keys / .env)"]
        end

        subgraph ModeB_Proc["Mode B: AST Pedagogical Compiler"]
            B1["Beat Script Generator (Local LLM)"]
            B2["Tree-Sitter Syntax & 42-Char Line Gate"]
            B3["Local Neural TTS + Millisecond Bookmark Sync"]
        end
    end

    subgraph Bridge["3. Declarative Intermediate Representation"]
        ReelIR[("Unified Reel-IR Document\n- 5-Track Declarative Timeline\n- Word Timestamps & Prov Badges\n- Viewport Keyframes & Code Cards\n- SafeCohort Redaction Boxes\n- Pedagogical Archetype Templates\n- Social Growth Pack & Outro QR\n- Dead-Air Hyperlapse Intervals")]
    end

    subgraph Studio["4. Interactive Studio & HITL Review"]
        UI_Review["Interactive Timeline & Provenance UI\n- Checkpoint 1: OCR Provenance Inspection\n- Checkpoint 2: Sentence-Snap Boundary Trim\n- Checkpoint 3: Layout Mode Selection\n- Checkpoint 4: Live Brand Kit & Archetype Config\n- Checkpoint 5: SafeCohort Blur & QR Review\n- SnipShot Local ROI Telemetry (₹0 Cloud Cost)"]
    end

    subgraph Output["5. Deterministic Composition & Delivery"]
        Renderer["Pillow HUD Synthesizer + FFmpeg Subprocess Pipe\n- cv2.GaussianBlur on Redaction Boxes\n- Dead-Air 2.5x Typing Hyperlapse\n- Dynamic Header Color Shift (Bug Hunter)\n- qrcode Library Outro Scan-to-Copy Stamp"]
        ExportMP4["Final 1080x1920 9:16 Branded Reel MP4\n- High-Contrast Monospace Code Cards\n- Synchronized Karaoke Word Captions\n- Dynamic Dual-ROI SplitStage Viewport\n- Redacted Secrets & Outro Code QR"]
        FeedbackLoop["Telemetry & PedagogyScore Feedback\n- Re-ranks highlight weights via Bandit update"]
    end

    InputA --> A1 & A2
    A2 --> A3
    A3 -->|Dynamic Hotwords| A4
    A3 --> A8
    InputA --> A4
    A3 & A4 --> A5
    A1 & A2 & A5 --> A6
    A5 & A2 --> A7
    A6 & A7 & A8 --> ReelIR

    InputB --> B1 --> B2 --> B3 --> ReelIR

    ReelIR <--> UI_Review
    UI_Review -->|Approved Configuration| Renderer
    Renderer --> ExportMP4
    ExportMP4 -.-> FeedbackLoop
    FeedbackLoop -.->|Updated Weights w1..w5| A6
```

---

## 2. Mode A Pipeline: Screen-Grounded Decompiler

Mode A processes an unedited 16:9 lecture video into complete-thought 9:16 educational clips. The sequence diagram below shows how the visual screen stream and audio stream interact through the **Time-Aligned Screen-Speech Graph (TSSG)**.

```mermaid
sequenceDiagram
    autonumber
    actor User as Instructor / Editor
    participant API as FastAPI Ingestion Router
    participant Plateau as Plateau Detector (OpenCV)
    participant OCR as ScreenLex Miner (RapidOCR)
    participant ASR as Biased ASR (faster-whisper)
    participant Repair as Phonetic-Visual Repair
    participant TSSG as TSSG Builder
    participant Clipper as ClosedThought Scorer
    participant Reframer as Smart 9:16 Reframer
    participant DB as Cache & Reel-IR Store

    User->>API: Upload 16:9 Lecture MP4
    API->>API: Compute SHA-256 Hash & Check Cache
    
    par Visual Stream Processing
        API->>Plateau: Ingest video at 2 FPS (480x270 greyscale)
        Plateau->>Plateau: Detect stable visual plateaus (absdiff < threshold)
        Plateau-->>OCR: Extract stabilized 1080p keyframes
        OCR->>OCR: Run CLAHE contrast filter & RapidOCR
        OCR->>OCR: Filter identifiers (camelCase, @decorators, CLI)
        OCR-->>TSSG: Register ScreenTokens with [x, y, w, h] & timestamps
        OCR->>OCR: SafeCohort Scanner runs regex & entropy analysis on token boxes
        OCR-->>TSSG: Register RedactionBoxes [x, y, w, h] (API keys, .env secrets, PII)
    and Audio Stream Processing
        API->>ASR: Extract 16kHz mono audio WAV
        OCR-->>ASR: Provide top 60 screen identifiers for hotwords & prompt
        ASR->>ASR: Execute faster-whisper (Romanized Hinglish prompt)
        ASR->>ASR: Compute DTW word alignments via stable-ts
        ASR-->>Repair: Raw ASRWord stream (p_conf, start, end)
    end

    Repair->>TSSG: Query screen tokens visible in [t - 20s, t + 20s]
    Repair->>Repair: Compute Metaphone + Jaro-Winkler phonetic similarity
    Note over Repair: Merges 'use a fact' into 'useEffect' (Sim >= 0.82)
    Repair->>TSSG: Commit repaired WordAlignment stream with OCR provenance badges
    TSSG->>TSSG: Detect silent typing intervals > 1.2s for 2.5x Hyperlapse speedup

    TSSG->>Clipper: Transmit synchronized screen-speech multimodal nodes
    Clipper->>Clipper: Evaluate 30-60s candidate windows
    Clipper->>Clipper: Compute Triad Score (Hook + Mutation + Verification)
    Clipper->>Clipper: Apply Deictic Penalty on dangling pronouns ('isko...')
    Clipper->>Clipper: Snap start and end to complete sentence boundaries
    Clipper->>Clipper: Classify Template Archetype (standard, bug_hunter, vs_battle, predict_output)
    Clipper->>Clipper: Generate Social Growth Pack (tiered hashtags, hook title, QR data)
    Clipper-->>Reframer: Top-scored clip interval [T_start, T_end] + Metadata

    Reframer->>Reframer: Analyze spatial activity & code line widths in [T_start, T_end]
    alt Single compact active region (width <= 850px)
        Reframer->>Reframer: Compute L1 Dead-Zone smoothed camera trajectory
    else Coupled IDE + Terminal activity (Left / Right split)
        Reframer->>Reframer: Trigger Dual-ROI SplitStage (Top 60% / Bottom 40%)
    else Active line width > 850px
        Reframer->>Reframer: Trigger Readable916 AST Code Spotlight Card
    end

    Reframer-->>DB: Assemble and persist initial Reel-IR JSON (with RedactionBoxes & Archetypes)
    DB-->>User: Return Reel-IR payload to Studio Timeline UI
```

---

## 3. Mode B Pipeline: AST-Verified Pedagogical Compiler

Mode B compiles an educational topic prompt into a high-trust, syntax-validated 9:16 code explainer reel. The pipeline enforces a strict AST gate to ensure that no broken code or illegible lines ever reach production.

```mermaid
sequenceDiagram
    autonumber
    actor User as Instructor / Operator
    participant Studio as Studio UI (Mode B)
    participant Compiler as Mode B Compiler
    participant LLM as Local Qwen2.5-Coder (or Cloud)
    participant Gate as Tree-Sitter Syntax Gate
    participant TTS as Neural TTS (Kokoro / Piper)
    participant Compositor as Pillow + FFmpeg Compositor

    User->>Studio: Enter Topic Prompt (e.g., 'JSON vs XML in Spring Boot')
    Studio->>Compiler: POST /api/explainer/generate (prompt, brand_kit_id)
    
    Compiler->>LLM: Request 4-Beat Explainer Script (JSON format)
    LLM-->>Compiler: Return raw beats: {hook, concept_a, concept_b, summary}

    loop AST & Mobile Legibility Verification
        Compiler->>Gate: Validate code snippets across all beats
        Gate->>Gate: Run py-tree-sitter concrete syntax parse
        Gate->>Gate: Check line length (max 42 chars) & total lines (max 14)
        alt Syntax error or line > 42 chars detected
            Gate-->>Compiler: Return AST failure details & offending line
            Compiler->>LLM: Re-prompt with exact syntax error & constraint rules
            LLM-->>Compiler: Return corrected code snippet
        else Code is 100% valid & legible
            Gate-->>Compiler: Pass validation (0 errors, max_width <= 42)
        end
    end

    loop Audio Narration & Timing Synchronization
        Compiler->>TTS: Synthesize voiceover per beat (Beat 1 to Beat 4)
        TTS->>TTS: Generate 24kHz studio audio WAV
        TTS->>TTS: Extract phoneme & word durations in milliseconds
        TTS-->>Compiler: Return WAV segment & exact duration d_k
        Compiler->>Compiler: Lock animation frame count F_k = floor(d_k * 30 fps)
    end

    Compiler->>Compiler: Concatenate audio & assemble Reel-IR schema
    Compiler-->>Studio: Return completed Reel-IR JSON for live playback
    User->>Studio: Review typing animation & click 'Export'
    Studio->>Compositor: Trigger render pipeline
    Compositor-->>User: Deliver finished 1080x1920 MP4
```

---

## 4. Video Rendering & Composition Pipeline

This flowchart details how the declarative 5-track `Reel-IR` document is transformed into a broadcast-quality 1080×1920 MP4 video without using heavy browser-based tools.

```mermaid
flowchart TD
    subgraph InputState["Reel-IR Timeline Document"]
        IR_Audio["Track 1: Audio Track (16kHz / 48kHz WAV)"]
        IR_Transcript["Track 2: Word Alignments (Timestamps & Badges)"]
        IR_Viewports["Track 3: Viewport Keyframes (Single / SplitStage)"]
        IR_CodeCards["Track 4: Code Spotlight Cards (Syntax & Highlight)"]
        IR_Brand["Track 5: Brand Kit (Colors, Fonts, Watermarks, Bumpers)"]
        IR_Security["SafeCohort: Redaction Boxes (Bounding boxes & intervals)"]
        IR_Archetype["Pedagogical Archetype (standard / bug_hunter / vs_battle / predict_output)"]
        IR_Growth["Social Growth Pack & Outro QR (Scan-to-copy code snippet)"]
        IR_Hyperlapse["Dead-Air Typing Intervals (>1.2s silent typing @ 2.5x)"]
    end

    subgraph CompositionEngine["Pillow + FFmpeg Frame Streaming Engine"]
        Clock["Timeline Clock (t = 0.00s to t = T_end, step = 1/30s)\n- Speed scaled by 2.5x during Hyperlapse intervals"]
        
        subgraph FrameSynthesizer["Per-Frame Generator (Python in-memory)"]
            BaseCrop["1. Source Video Crop & Resize\n- Single: Crop 1920x1080 via L1 Box\n- SplitStage: Crop Upper IDE + Lower Terminal"]
            BlurShield["2. SafeCohort Secret Blur\n- Localized cv2.GaussianBlur over RedactionBoxes\n- Obscures API keys, .env secrets, passwords, PII"]
            ArchetypeLayer["3. Pedagogical Archetype Styling\n- Bug Hunter: Dynamic Crimson -> Emerald header at error_resolved_at\n- VS Battle: Top Legacy vs Bottom Modern comparison cards\n- Predict Output: 2s freeze-frame callout"]
            CodeOverlay["4. Pygments Syntax Card\n- Render active code card with highlighted lines\n- Monospace 32px font, 100% mobile legible"]
            Captions["5. Word-by-Word Karaoke HUD\n- Subtitle pill box with Brand Cyan highlight & provenance badge"]
            BrandLayer["6. Brand Layering & Outro QR Stamp\n- Header watermark & Institute Logo\n- Progress bar at bottom edge\n- Outro Bumper with offline qrcode for code copying"]
        end

        BufferPipe["In-Memory Raw Video Pipe (stdout -> stdin)\n- 1080x1920 @ 30fps RGBA / YUV420p"]
    end

    subgraph FFmpegProcess["FFmpeg Hardware/CPU Subprocess"]
        Encoder["FFmpeg Process Configuration\n- Input: rawvideo -pix_fmt yuv420p -s 1080x1920\n- Audio Input: -i audio.wav (with atempo filter during hyperlapse)\n- Video Codec: libx264 (preset: fast, crf: 20)\n  or h264_nvenc (if NVIDIA GPU detected)"]
        BumperStitch["Intro/Outro Bumper Concatenation Filter (with QR Stamp)"]
        DiskWriter["Atomic Output MP4 File Generator"]
    end

    IR_Audio & IR_Hyperlapse --> Clock
    IR_Transcript & IR_Viewports & IR_CodeCards & IR_Brand & IR_Security & IR_Archetype & IR_Growth --> FrameSynthesizer
    Clock --> FrameSynthesizer
    BaseCrop --> BlurShield --> ArchetypeLayer --> CodeOverlay --> Captions --> BrandLayer --> BufferPipe
    BufferPipe --> Encoder
    IR_Audio --> Encoder
    Encoder --> BumperStitch --> DiskWriter
    DiskWriter --> Done["Deliver Ready-to-Publish 9:16 Video"]
```

---

## 5. Human-in-the-Loop (HITL) Validation Checkpoints

SnipShot integrates five explicit validation checkpoints where the instructor or editor can inspect, adjust, and approve AI-generated choices before video export.

```mermaid
stateDiagram-v2
    [*] --> IngestionComplete: Raw Video Processed into TSSG
    
    state IngestionComplete {
        [*] --> CandidateReview
        CandidateReview: 3 Candidate Clips Presented with Triad Scores
    }

    IngestionComplete --> Checkpoint1: Select Candidate Clip

    state Checkpoint1 {
        [*] --> InspectTranscript
        InspectTranscript: Review words highlighted with Cyan Provenance Badges
        InspectTranscript --> VerifyProof: Click Badge (e.g. 'useEffect')
        VerifyProof: View side-by-side comparison:\n- Raw ASR: 'use a fact' (p=0.48)\n- OCR Match: 'useEffect' (sim=0.91)\n- Cropped IDE Pixel Proof
        VerifyProof --> ManualOverride: Disapprove correction?
        ManualOverride: Type custom replacement or revert to raw
        ManualOverride --> InspectTranscript
        VerifyProof --> TermApproved: Approve correction
    }

    Checkpoint1 --> Checkpoint2: Proceed to Boundary Review

    state Checkpoint2 {
        [*] --> ScrubWaveform
        ScrubWaveform: Inspect audio waveform on WaveSurfer track
        ScrubWaveform --> DragHandles: Drag Start / End Boundary Handles
        DragHandles: Handles automatically snap to complete sentence boundaries
        DragHandles --> ValidateClosure: System checks Deictic Entry and Terminal Output
    }

    Checkpoint2 --> Checkpoint3: Proceed to Layout Review

    state Checkpoint3 {
        [*] --> InspectLayout
        InspectLayout: Preview 9:16 frame in Studio Canvas
        InspectLayout --> SwitchMode: Override AI layout decision
        SwitchMode: Toggle between:\n1. Damped Single Focus\n2. Dual-ROI SplitStage\n3. AST Code Spotlight Card
    }

    Checkpoint3 --> Checkpoint4: Proceed to Brand & Archetype

    state Checkpoint4 {
        [*] --> ApplyBrandKit
        ApplyBrandKit: Select Institute Brand Kit\n(Colors, Fonts, Watermark, Outro)
        ApplyBrandKit --> SelectArchetype: Pick Pedagogical Archetype\n(Standard, Bug Hunter, VS Battle, Predict Output)
        SelectArchetype --> ArchetypePreview: Preview dynamic color shifts or split cards
    }

    Checkpoint4 --> Checkpoint5: Proceed to Security & Growth Pack

    state Checkpoint5 {
        [*] --> SafeCohortReview
        SafeCohortReview: Inspect detected secrets (API keys, .env, PII)\nToggle Gaussian blur boxes on/off
        SafeCohortReview --> GrowthPackReview: Inspect SEO hook, tiered hashtags & Outro QR Code
        GrowthPackReview --> LocalROITelemetry: View SnipShot Local ROI Telemetry\n(₹0.00 Cloud Cost, Credits Saved, 100% On-Device Privacy)
        LocalROITelemetry --> FastPreview: Fast Sub-10s Preview Re-Render
        FastPreview --> ExportFinal: Approve for Final 1080x1920 MP4 Export
    }

    Checkpoint5 --> [*]: Video Downloaded / Scheduled
```

---

## 6. Error Handling & Fallback Decision Matrix

This flowchart details how the system gracefully handles real-world edge cases (dark themes, high CPU load, Hinglish script drift, LLM timeouts, and exposed secrets) without failing or producing corrupted outputs.

```mermaid
flowchart TD
    subgraph EdgeCase1["Edge Case 1: Dark-Theme / Low-Contrast IDE OCR"]
        E1_In["Plateau Frame Received"] --> E1_Check{"OCR Confidence < 0.60 or 0 tokens found?"}
        E1_Check -- No --> E1_Normal["Proceed with standard RapidOCR tokens"]
        E1_Check -- Yes --> E1_Filter["Apply OpenCV Inversion + CLAHE Filter\n(Contrast Limited Adaptive Histogram Equalization)"]
        E1_Filter --> E1_Retry["Re-run RapidOCR on pre-filtered frame"]
        E1_Retry --> E1_Eval{"Tokens recovered?"}
        E1_Eval -- Yes --> E1_Normal
        E1_Eval -- No --> E1_Glossary["Fall back to Base Domain Glossary (tech_glossary.json)\n(2,000+ curated CS terms)"]
    end

    subgraph EdgeCase2["Edge Case 2: Hinglish Script Alternation in Whisper"]
        E2_In["Raw ASR Word Stream"] --> E2_Check{"Contains mixed Devanagari script?"}
        E2_Check -- No --> E2_Clean["Romanized Hinglish stream confirmed"]
        E2_Check -- Yes --> E2_Translit["Run Deterministic Indic-Transliteration\n(Convert Devanagari tokens to Romanized Hinglish)"]
        E2_Translit --> E2_Case["Enforce Technical Casing Rule\n(Restore camelCase / PascalCase for identifiers)"]
        E2_Case --> E2_Clean
    end

    subgraph EdgeCase3["Edge Case 3: Memory Constraint on 8GB / 16GB CPU Laptop"]
        E3_In["Pipeline Stage Transition"] --> E3_Monitor{"Host Available RAM < 2.5 GB?"}
        E3_Monitor -- No --> E3_Continue["Proceed with default parallel execution"]
        E3_Monitor -- Yes --> E3_Seq["Trigger Sequential Memory Management:"]
        E3_Seq --> E3_U1["1. Unload RapidOCR ONNX session & run gc.collect()"]
        E3_Seq --> E3_U2["2. Run faster-whisper int8 transcription"]
        E3_Seq --> E3_U3["3. Delete Whisper model object & run gc.collect()"]
        E3_Seq --> E3_U4["4. Execute LLM / Heuristic scoring in isolated memory"]
        E3_U4 --> E3_Safe["Zero OOM Crashes Guaranteed"]
    end

    subgraph EdgeCase4["Edge Case 4: Mode B LLM Offline or Generation Timeout"]
        E4_In["Mode B Prompt Submitted"] --> E4_Timeout{"LLM response takes > 20s or connection error?"}
        E4_Timeout -- No --> E4_Success["Use LLM-generated beat script"]
        E4_Timeout -- Yes --> E4_Fallback["Activate Deterministic AST Template Engine"]
        E4_Fallback --> E4_Build["Construct validated comparison layout from template library\n(Pre-validated syntax & 42-char layout)"]
        E4_Build --> E4_Success
    end

    subgraph EdgeCase5["Edge Case 5: Accidental Secret or PII Leak in Screen Recording"]
        E5_In["Extracted OCR Tokens"] --> E5_Scan{"Matches secret regex (sk-, AWS, password, .env) or high Shannon entropy?"}
        E5_Scan -- No --> E5_Pass["Mark frame tokens safe"]
        E5_Scan -- Yes --> E5_Redact["Register RedactionBox with coordinates [x, y, w, h] in ReelIR"]
        E5_Redact --> E5_Blur["Compositor applies cv2.GaussianBlur over bounding box across visible interval"]
        E5_Blur --> E5_Alert["Display SafeCohort active shield badge in Studio UI & Telemetry"]
    end
```

---

## 7. Telemetry & Continuous Optimization Feedback Loop

To continuously improve highlight selection accuracy, SnipShot includes a lightweight `PedagogyScore` feedback loop powered by a contextual bandit algorithm.

```mermaid
flowchart LR
    subgraph ReelStudio["Reel Studio Production Engine"]
        Scorer["ClosedThought Highlight Scorer\nw1*Prosody + w2*Visual + w3*Tech + w4*Triad - w5*Deictic"]
        Publisher["Export & Publish Reel"]
    end

    subgraph AudienceTelemetry["Viewer Engagement Ingestion"]
        Metrics["Audience Telemetry Input\n- 3-Second Retention Rate\n- 100% Video Completion Rate\n- Comment / Share Signals"]
    end

    subgraph BanditEngine["PedagogyScore Contextual Bandit"]
        Loss["Compute Pedagogical Reward R:\nR = 0.5 * Completion + 0.3 * Retention + 0.2 * TechDensity"]
        Gradient["LinUCB / Gradient Weight Update:\nDelta_w = alpha * (R - Expected_R) * Feature_Vector"]
        UpdateWeights["Update Weights:\nw_triad increased (+), w_prosody adjusted (-)"]
    end

    Scorer --> Publisher
    Publisher --> Metrics
    Metrics --> Loss
    Loss --> Gradient
    Gradient --> UpdateWeights
    UpdateWeights -->|Persist to snipshot.db| Scorer
```
