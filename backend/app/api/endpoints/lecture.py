"""
Lecture Endpoints (Mode A: Screen-Grounded Decompiler).
Handles video upload, sparse plateau detection, screen OCR, grounded Hinglish ASR,
phonetic repair, highlight extraction, and 9:16 viewport retargeting.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from typing import List
import os
import shutil
import uuid
from pathlib import Path

from backend.app.schemas.reel_ir import ReelIR
from backend.app.schemas.api_requests import AnalyzeLectureResponse
from backend.app.core.plateau_detector import PlateauDetector
from backend.app.core.screen_lex_ocr import ScreenLexMiner
from backend.app.core.grounded_asr import GroundedASR
from backend.app.core.phonetic_repair import PhoneticVisualRepairer
from backend.app.core.closed_thought import ClosedThoughtClipper
from backend.app.core.smart_reframer import SmartReframer
from backend.app.core.tssg_builder import TSSGBuilder
from backend.app.services.ffmpeg_service import FFmpegService
from backend.app.config import settings

router = APIRouter()
ffmpeg_service = FFmpegService()


@router.post("/analyze", response_model=AnalyzeLectureResponse)
async def analyze_lecture(
    file: UploadFile = File(...),
):
    """
    Ingests 16:9 lecture recording, runs SGPC pipeline, and returns top 3 candidate Reel-IR clips.
    """
    video_id = f"lecture_{uuid.uuid4().hex[:8]}"
    upload_path = settings.UPLOAD_DIR / f"{video_id}.mp4"
    audio_path = settings.CACHE_DIR / f"{video_id}_audio.wav"

    # Save uploaded video
    try:
        with open(upload_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save video: {str(e)}")

    # 1. Probe video
    probe_info = ffmpeg_service.probe_video(str(upload_path))
    duration = probe_info.get("duration", 60.0)

    # 2. Extract 16kHz mono audio WAV
    try:
        ffmpeg_service.extract_audio(str(upload_path), str(audio_path))
    except Exception:
        pass

    # 3. Detect visual plateaus (2 FPS absdiff)
    plateau_detector = PlateauDetector(output_dir=settings.CACHE_DIR / "keyframes")
    plateau_frames, diff_events = plateau_detector.detect_plateaus(str(upload_path))

    # 4. Extract screen tokens via RapidOCR + Identifier filter
    ocr_miner = ScreenLexMiner()
    screen_tokens = ocr_miner.extract_screen_tokens(plateau_frames)

    # 5. Grounded Hinglish ASR (ScreenLex Pass 1)
    asr_engine = GroundedASR()
    asr_words = asr_engine.transcribe(str(audio_path), screen_tokens)
    asr_engine.unload_model()  # Free memory immediately!

    # 6. Phonetic-Surface Repair (ScreenLex Pass 2)
    repairer = PhoneticVisualRepairer()
    repaired_words = repairer.repair_transcript(asr_words, screen_tokens)

    # 7. ClosedThought Pedagogical Triad Highlight Extraction
    clipper = ClosedThoughtClipper()
    candidate_spans = clipper.extract_highlights(repaired_words, diff_events, top_k=3)

    # 8. Smart 9:16 Viewport Retargeting for each candidate span
    reframer = SmartReframer()
    candidate_reels: List[ReelIR] = []

    for idx, span in enumerate(candidate_spans):
        span_words = [w for w in repaired_words if span.start_time <= w.start <= span.end_time]
        # Shift word timestamps relative to clip start
        shifted_words = []
        for w in span_words:
            shifted = w.model_copy()
            shifted.start = round(max(0.0, w.start - span.start_time), 3)
            shifted.end = round(max(0.0, w.end - span.start_time), 3)
            shifted_words.append(shifted)

        viewports, code_cards, layout_mode = reframer.compute_viewports(
            span.start_time, span.end_time, screen_tokens, diff_events
        )

        reel = ReelIR(
            schema_version="1.0.0",
            reel_id=f"{video_id}_clip_{idx + 1}",
            mode="mode_a_extract",
            title=f"Highlight #{idx + 1}: {span.first_phrase[:35]}...",
            source_media_path=str(upload_path),
            clip_start=span.start_time,
            clip_end=span.end_time,
            total_duration=round(span.duration, 2),
            audio_path=str(audio_path),
            transcript=shifted_words,
            viewports=viewports,
            code_cards=code_cards,
            pedagogical_score=span.triad_score,
            entry_closure_verified=not span.deictic_penalized,
            exit_closure_verified=True,
            technical_term_count=sum(1 for w in shifted_words if w.is_technical),
        )
        candidate_reels.append(reel)

    return AnalyzeLectureResponse(
        video_id=video_id,
        duration_seconds=duration,
        plateau_frames_count=len(plateau_frames),
        extracted_tokens_count=len(screen_tokens),
        candidate_clips=candidate_reels,
    )
