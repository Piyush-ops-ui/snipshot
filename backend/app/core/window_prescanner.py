"""
Window Pre-Scanner:
Ultra-fast video prescanner that analyzes audio energy and sparse 1-FPS visual diffs.
For short videos (<= 360s / 6 mins), selects the full duration.
For long videos (10 mins to 2 hours), identifies the top 3 most active 2-minute teaching windows in < 4 seconds.
"""

from dataclasses import dataclass, asdict
from typing import List, Tuple, Optional
from pathlib import Path
import os
import subprocess
import numpy as np

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    cv2 = None
    CV2_AVAILABLE = False

try:
    from scipy.io import wavfile
    SCIPY_AVAILABLE = True
except ImportError:
    wavfile = None
    SCIPY_AVAILABLE = False

from backend.app.services.ffmpeg_service import FFmpegService
from backend.app.config import settings


@dataclass
class TeachingWindow:
    start_sec: float
    end_sec: float
    score: float
    audio_rms: float = 0.0
    visual_diff: float = 0.0

    def to_dict(self):
        return asdict(self)


class WindowPreScanner:
    def __init__(
        self,
        ffmpeg_service: Optional[FFmpegService] = None,
        cache_dir: Optional[Path] = None,
    ):
        self.ffmpeg = ffmpeg_service or FFmpegService()
        self.cache_dir = cache_dir or (settings.CACHE_DIR / "prescan")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def extract_audio_16k(self, video_path: str, output_wav_path: Optional[str] = None) -> str:
        """Extracts 16kHz mono PCM WAV via FFmpeg."""
        if not output_wav_path:
            video_name = Path(video_path).stem
            output_wav_path = str(self.cache_dir / f"{video_name}_16k.wav")

        if os.path.exists(output_wav_path) and os.path.getsize(output_wav_path) > 1024:
            return output_wav_path

        self.ffmpeg.extract_audio(video_path, output_wav_path)
        return output_wav_path

    def compute_1s_audio_rms(self, wav_path: str, total_seconds: int) -> np.ndarray:
        """Computes 1-second RMS audio energy vector."""
        if not os.path.exists(wav_path) or total_seconds <= 0:
            return np.zeros(total_seconds, dtype=np.float32)

        try:
            if SCIPY_AVAILABLE:
                sr, data = wavfile.read(wav_path)
            else:
                import wave
                with wave.open(wav_path, "rb") as wf:
                    sr = wf.getframerate()
                    raw = wf.readframes(wf.getnframes())
                    data = np.frombuffer(raw, dtype=np.int16)

            if data.ndim > 1:
                data = np.mean(data, axis=1)

            data = data.astype(np.float32)
            if data.dtype == np.int16:
                data /= 32768.0

            rms_per_sec = np.zeros(total_seconds, dtype=np.float32)
            for s in range(total_seconds):
                chunk = data[s * sr : (s + 1) * sr]
                if len(chunk) > 0:
                    rms_per_sec[s] = float(np.sqrt(np.mean(chunk**2)))

            max_rms = float(np.max(rms_per_sec)) if len(rms_per_sec) > 0 else 0.0
            if max_rms > 1e-6:
                rms_per_sec /= max_rms

            return rms_per_sec
        except Exception:
            return np.zeros(total_seconds, dtype=np.float32)

    def compute_sparse_1fps_diff(
        self, video_path: str, total_seconds: int, fps: float
    ) -> np.ndarray:
        """
        Computes sparse 1-FPS frame diff across the video in seconds.
        Skips ~30 frames at a time, downsamples to 160x90 grayscale for ultra-fast diffing.
        """
        diff_per_sec = np.zeros(total_seconds, dtype=np.float32)
        if not CV2_AVAILABLE or not os.path.exists(video_path) or total_seconds <= 0:
            return diff_per_sec

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return diff_per_sec

        try:
            prev_gray = None
            step_fps = max(1, int(round(fps)))

            for s in range(total_seconds):
                frame_idx = s * step_fps
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                if not ret or frame is None:
                    continue

                # Downsample to small thumbnail for instant diffing
                small = cv2.resize(frame, (160, 90), interpolation=cv2.INTER_NEAREST)
                gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)

                if prev_gray is not None:
                    diff = float(np.mean(cv2.absdiff(gray, prev_gray)) / 255.0)
                    diff_per_sec[s] = diff

                prev_gray = gray

            max_diff = float(np.max(diff_per_sec)) if len(diff_per_sec) > 0 else 0.0
            if max_diff > 1e-6:
                diff_per_sec /= max_diff

            return diff_per_sec
        finally:
            cap.release()

    def scan_video(
        self,
        video_path: str,
        audio_path: Optional[str] = None,
        window_duration: float = 120.0,
        top_k: int = 3,
    ) -> Tuple[List[TeachingWindow], str]:
        """
        Fast Window Pre-Scanner:
        Given any video path:
        1. Extract audio at 16kHz via ffmpeg.
        2. If duration <= 360s (6 mins), return entire video span [0, duration].
        3. If duration > 360s (e.g. 10m to 2h), compute 1s RMS audio energy + sparse 1-FPS frame diff
           to rank and select top 3 most active 2-minute teaching windows.
        """
        probe = self.ffmpeg.probe_video(video_path)
        duration = float(probe.get("duration", 0.0))
        fps = float(probe.get("fps", 30.0))

        if duration <= 0.0:
            # Fallback probe with OpenCV
            if CV2_AVAILABLE and os.path.exists(video_path):
                cap = cv2.VideoCapture(video_path)
                fcount = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                cfps = cap.get(cv2.CAP_PROP_FPS) or 30.0
                duration = fcount / cfps if cfps > 0 else 60.0
                fps = cfps
                cap.release()

        duration = max(1.0, duration)
        wav_path = self.extract_audio_16k(video_path, audio_path)

        # Rule 1: Videos <= 360s (6 mins) -> Return full video span
        if duration <= 360.0:
            single_window = TeachingWindow(
                start_sec=0.0,
                end_sec=round(duration, 2),
                score=1.0,
                audio_rms=1.0,
                visual_diff=1.0,
            )
            return [single_window], wav_path

        # Rule 2: Videos > 360s -> Rank top active windows
        total_secs = int(duration)
        audio_rms = self.compute_1s_audio_rms(wav_path, total_secs)
        visual_diff = self.compute_sparse_1fps_diff(video_path, total_secs, fps)

        # Combined 1-second activity score
        activity_1s = 0.5 * audio_rms + 0.5 * visual_diff

        win_len = int(window_duration)
        if total_secs <= win_len:
            single_window = TeachingWindow(
                start_sec=0.0,
                end_sec=round(duration, 2),
                score=1.0,
                audio_rms=float(np.mean(audio_rms)),
                visual_diff=float(np.mean(visual_diff)),
            )
            return [single_window], wav_path

        step = 15  # 15s stride for window candidates
        candidates: List[TeachingWindow] = []

        for start_s in range(0, total_secs - win_len + 1, step):
            end_s = start_s + win_len
            w_act = activity_1s[start_s:end_s]
            w_rms = float(np.mean(audio_rms[start_s:end_s]))
            w_diff = float(np.mean(visual_diff[start_s:end_s]))
            mean_score = float(np.mean(w_act))

            candidates.append(
                TeachingWindow(
                    start_sec=float(start_s),
                    end_sec=float(end_s),
                    score=round(mean_score, 4),
                    audio_rms=round(w_rms, 4),
                    visual_diff=round(w_diff, 4),
                )
            )

        # Non-Maximum Suppression (NMS) to get non-overlapping diverse top windows
        candidates.sort(key=lambda w: w.score, reverse=True)
        selected_windows: List[TeachingWindow] = []
        min_separation = 60.0  # At least 60 seconds separation between window starts

        for cand in candidates:
            if len(selected_windows) >= top_k:
                break
            overlap = False
            for sel in selected_windows:
                if abs(cand.start_sec - sel.start_sec) < min_separation:
                    overlap = True
                    break
            if not overlap:
                selected_windows.append(cand)

        # Fallback if NMS eliminated too many
        if len(selected_windows) < top_k:
            for cand in candidates:
                if len(selected_windows) >= top_k:
                    break
                if cand not in selected_windows:
                    selected_windows.append(cand)

        # Sort selected windows chronologically
        selected_windows.sort(key=lambda w: w.start_sec)
        return selected_windows, wav_path
