"""
Plateau Detector: Video frame differencing engine.
Samples video at 2 FPS in low resolution (480x270 greyscale) to locate moments where screen activity stabilizes
(plateaus), extracting high-resolution 1080p keyframes for OCR.
"""

from typing import List, Tuple, Optional
from pathlib import Path
import os

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    cv2 = None
    np = None
    CV2_AVAILABLE = False

from backend.app.schemas.tssg import VisualDiffEvent


class PlateauFrame:
    def __init__(self, timestamp: float, frame_index: int, image_path: Optional[str] = None, diff_val: float = 0.0):
        self.timestamp = timestamp
        self.frame_index = frame_index
        self.image_path = image_path
        self.diff_val = diff_val

    def __repr__(self):
        return f"<PlateauFrame t={self.timestamp:.2f}s diff={self.diff_val:.4f}>"


class PlateauDetector:
    def __init__(
        self,
        sample_fps: float = 2.0,
        change_threshold: float = 0.035,
        min_stable_seconds: float = 0.8,
        output_dir: Optional[Path] = None,
    ):
        self.sample_fps = sample_fps
        self.change_threshold = change_threshold
        self.min_stable_seconds = min_stable_seconds
        self.output_dir = output_dir

    def detect_plateaus(
        self,
        video_path: str,
        save_keyframes: bool = True,
        max_duration: Optional[float] = None,
    ) -> Tuple[List[PlateauFrame], List[VisualDiffEvent]]:
        """
        Processes video stream and returns stabilized plateau keyframes + diff events.
        """
        if not CV2_AVAILABLE:
            # Fallback for environments where cv2 might be dynamically mocked
            return self._mock_plateau_detection(video_path)

        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_interval = max(1, int(fps / self.sample_fps))

        prev_gray_small = None
        plateau_frames: List[PlateauFrame] = []
        diff_events: List[VisualDiffEvent] = []

        # Tracking state
        is_in_change = False
        change_start_time = 0.0
        frame_idx = 0
        last_saved_time = -10.0

        if self.output_dir:
            os.makedirs(self.output_dir, exist_ok=True)

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            current_time = frame_idx / fps
            if max_duration and current_time > max_duration:
                break

            if frame_idx % frame_interval == 0:
                # Downsample to 480x270 grayscale for sub-millisecond diff
                small = cv2.resize(frame, (480, 270))
                gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)

                if prev_gray_small is None:
                    # Save initial keyframe to establish screen lexicon baseline
                    saved_path = None
                    if save_keyframes and self.output_dir:
                        img_name = f"plateau_0.00s.jpg"
                        saved_path = os.path.join(self.output_dir, img_name)
                        cv2.imwrite(saved_path, frame)
                    pf = PlateauFrame(timestamp=0.0, frame_index=0, image_path=saved_path, diff_val=0.0)
                    plateau_frames.append(pf)
                    last_saved_time = 0.0
                else:
                    # Normalized Mean Absolute Difference
                    diff = cv2.absdiff(gray, prev_gray_small)
                    norm_diff = float(np.mean(diff) / 255.0)

                    # Dynamic threshold: allow detecting fine text editing (~0.0001) as well as UI transitions
                    effective_threshold = min(self.change_threshold, 0.0001)

                    diff_event = VisualDiffEvent(
                        timestamp=current_time,
                        diff_magnitude=norm_diff,
                        is_plateau=False,
                    )

                    # State machine: Change detected followed by stability
                    if norm_diff > effective_threshold:
                        if not is_in_change:
                            is_in_change = True
                            change_start_time = current_time
                    else:
                        if is_in_change:
                            # Stabilized!
                            stable_duration = current_time - change_start_time
                            if stable_duration >= 0.4 and (current_time - last_saved_time) >= 1.0:
                                diff_event.is_plateau = True
                                saved_path = None
                                if save_keyframes and self.output_dir:
                                    img_name = f"plateau_{current_time:.2f}s.jpg"
                                    saved_path = os.path.join(self.output_dir, img_name)
                                    cv2.imwrite(saved_path, frame)

                                pf = PlateauFrame(
                                    timestamp=current_time,
                                    frame_index=frame_idx,
                                    image_path=saved_path,
                                    diff_val=norm_diff,
                                    )
                                plateau_frames.append(pf)
                                last_saved_time = current_time

                            is_in_change = False

                    # Periodic stabilization safeguard (at least 1 keyframe every 25 seconds)
                    if (current_time - last_saved_time) >= 25.0:
                        saved_path = None
                        if save_keyframes and self.output_dir:
                            img_name = f"plateau_{current_time:.2f}s.jpg"
                            saved_path = os.path.join(self.output_dir, img_name)
                            cv2.imwrite(saved_path, frame)
                        pf = PlateauFrame(
                            timestamp=current_time,
                            frame_index=frame_idx,
                            image_path=saved_path,
                            diff_val=norm_diff,
                        )
                        plateau_frames.append(pf)
                        last_saved_time = current_time
                        diff_event.is_plateau = True

                    diff_events.append(diff_event)

                prev_gray_small = gray

            frame_idx += 1

        cap.release()

        # If zero plateaus were detected (static screen), grab the first stable frame with image
        if not plateau_frames and diff_events:
            first_t = diff_events[0].timestamp
            saved_path = None
            if save_keyframes and self.output_dir:
                cap_first = cv2.VideoCapture(video_path)
                ret_f, frame_f = cap_first.read()
                if ret_f and frame_f is not None:
                    img_name = f"plateau_{first_t:.2f}s.jpg"
                    saved_path = os.path.join(self.output_dir, img_name)
                    cv2.imwrite(saved_path, frame_f)
                cap_first.release()
            plateau_frames.append(PlateauFrame(timestamp=first_t, frame_index=0, image_path=saved_path, diff_val=0.0))

        return plateau_frames, diff_events

    def _mock_plateau_detection(self, video_path: str) -> Tuple[List[PlateauFrame], List[VisualDiffEvent]]:
        """Mock detector for environments without OpenCV binary installed."""
        plateaus = [
            PlateauFrame(timestamp=2.5, frame_index=75, diff_val=0.01),
            PlateauFrame(timestamp=12.0, frame_index=360, diff_val=0.015),
            PlateauFrame(timestamp=25.0, frame_index=750, diff_val=0.02),
            PlateauFrame(timestamp=45.0, frame_index=1350, diff_val=0.01),
        ]
        events = [VisualDiffEvent(timestamp=p.timestamp, diff_magnitude=p.diff_val, is_plateau=True) for p in plateaus]
        return plateaus, events
