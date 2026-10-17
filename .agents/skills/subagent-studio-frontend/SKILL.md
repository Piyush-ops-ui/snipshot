---
name: subagent-studio-frontend
description: Domain instructions and technical specifications for Subagent 4 (Interactive Studio UI Engineer) in SnipShot.
---

# Subagent 4: Interactive Studio UI Engineer

## Domain Boundary
- `frontend/src/components/*`
- `frontend/src/hooks/*`
- `frontend/src/services/*`
- `frontend/src/types/*`
- `frontend/package.json` & `frontend/vite.config.ts`

## Core Responsibilities & Anti-Hardcoding Mandate
1. **Weapon 10 Studio Header Bar (`Header.tsx`):**
   - Displays live local hardware status: `Intel Core Ultra 5 125H + Intel Arc QSV Active | ₹0.00 Cloud Cost | 100% On-Device Privacy`.
   - Displays real-time estimated SaaS subscription and per-minute credit savings compared to cloud wrappers.

2. **Side-by-Side Comparison Player (`SideBySidePlayer.tsx`):**
   - Plays Naive 16:9 Center-Crop + Raw Whisper alongside the SnipShot SGPC 9:16 vertical output to demonstrate technical superiority.

3. **Clickable OCR Provenance Inspector (`ProvenanceModal.tsx`):**
   - When the user clicks on any cyan-highlighted repaired technical term (`useEffect`, `@Autowired`, `Kubernetes`), opens an interactive modal displaying:
     - Side-by-side: Raw ASR (`"use a fact"`) vs Repaired Term (`useEffect`).
     - Phonetic + Jaro-Winkler match confidence score.
     - Actual cropped 1080p source video screenshot proof showing where the code token appeared on screen.

4. **Magnetic Sentence-Snap Timeline Editor (`MagneticTimeline.tsx`):**
   - Renders the interactive audio waveform using `WaveSurfer.js`.
   - Boundary handles automatically snap magnetically to complete sentence endings and audio pauses.
   - Allows users to preview cuts and trigger sub-10s fast re-renders.

5. **Brand Kit & Archetype Customization:**
   - Interactive selector for the 4 Pedagogical Archetypes (`standard_spotlight`, `bug_hunter`, `vs_battle`, `predict_output`).
   - Toggles SafeCohort secret blur boxes and customizes institute logos, typography, and accent colors.

6. **Growth Pack & Telemetry Drawer:**
   - One-click copy for tiered hashtags, pinned comments, and preview of the outro QR code badge.
