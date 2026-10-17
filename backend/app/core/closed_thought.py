"""
ClosedThought Triad Clipper:
Multimodal pedagogical highlight discovery engine.
Enforces the Pedagogical Triad (Hook -> Mutation -> Verification), computes real vocal energy RMS
via numpy/scipy, calculates visual typing diff density across plateau frames, penalizes dangling
Hinglish/English deictic pronouns, and magnetically snaps boundaries to sentence ends and pauses (>= 0.4s).
"""

from typing import List, Tuple, Optional, Dict, Union, Any
from pathlib import Path
import json
import re
import numpy as np

try:
    from scipy.io import wavfile
    SCIPY_AVAILABLE = True
except ImportError:
    wavfile = None
    SCIPY_AVAILABLE = False

from backend.app.schemas.reel_ir import WordAlignment
from backend.app.schemas.tssg import VisualDiffEvent
from backend.app.core.feedback_bandit import PedagogyScoreBandit
from backend.app.config import settings


class CandidateSpan:
    def __init__(
        self,
        start_index: int,
        end_index: int,
        start_time: float,
        end_time: float,
        triad_score: float,
        tech_density: float,
        deictic_penalized: bool,
        first_phrase: str,
        last_phrase: str,
        features: Optional[Dict[str, float]] = None,
        audio_rms: float = 0.0,
        visual_density: float = 0.0,
    ):
        self.start_index = start_index
        self.end_index = end_index
        self.start_time = start_time
        self.end_time = end_time
        self.triad_score = triad_score
        self.tech_density = tech_density
        self.deictic_penalized = deictic_penalized
        self.first_phrase = first_phrase
        self.last_phrase = last_phrase
        self.features = features or {}
        self.audio_rms = audio_rms
        self.visual_density = visual_density

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time

    def to_dict(self) -> Dict[str, Any]:
        return {
            "start_index": self.start_index,
            "end_index": self.end_index,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "triad_score": self.triad_score,
            "tech_density": self.tech_density,
            "deictic_penalized": self.deictic_penalized,
            "first_phrase": self.first_phrase,
            "last_phrase": self.last_phrase,
            "features": self.features,
            "audio_rms": self.audio_rms,
            "visual_density": self.visual_density,
        }


def compute_audio_rms(
    audio_source: Union[str, Path, np.ndarray, bytes],
    start_time: float,
    end_time: float,
    sample_rate: int = 16000,
) -> float:
    """
    Computes vocal energy Root Mean Square (RMS) via numpy/scipy across [start_time, end_time].
    Normalizes RMS to [0.0, 1.0].
    """
    if end_time <= start_time:
        return 0.0

    samples: Optional[np.ndarray] = None
    sr = sample_rate

    if isinstance(audio_source, (str, Path)):
        p = Path(audio_source)
        if not p.exists():
            return 0.0
        try:
            if SCIPY_AVAILABLE:
                file_sr, data = wavfile.read(str(p))
                sr = file_sr
                if data.ndim > 1:
                    data = np.mean(data, axis=1)
                if data.dtype == np.int16:
                    samples = data.astype(np.float32) / 32768.0
                elif data.dtype == np.int32:
                    samples = data.astype(np.float32) / 2147483648.0
                elif data.dtype == np.uint8:
                    samples = (data.astype(np.float32) - 128.0) / 128.0
                else:
                    samples = data.astype(np.float32)
            else:
                import wave
                with wave.open(str(p), "rb") as wf:
                    sr = wf.getframerate()
                    n_frames = wf.getnframes()
                    raw = wf.readframes(n_frames)
                    data = np.frombuffer(raw, dtype=np.int16)
                    samples = data.astype(np.float32) / 32768.0
        except Exception:
            return 0.0
    elif isinstance(audio_source, np.ndarray):
        samples = audio_source.astype(np.float32)
        if samples.ndim > 1:
            samples = np.mean(samples, axis=1)
        if np.max(np.abs(samples)) > 1.0:
            samples = samples / 32768.0

    if samples is None or len(samples) == 0:
        return 0.0

    s_idx = max(0, int(start_time * sr))
    e_idx = min(len(samples), int(end_time * sr))

    if e_idx <= s_idx:
        return 0.0

    slice_samples = samples[s_idx:e_idx]
    rms = float(np.sqrt(np.mean(slice_samples ** 2)))

    # Speech RMS typically peaks around 0.15 - 0.25; scale to [0.0, 1.0]
    normalized_rms = min(1.0, rms * 5.0)
    return round(normalized_rms, 4)


def compute_visual_typing_density(
    diff_events: List[VisualDiffEvent],
    start_t: float,
    end_t: float,
) -> Tuple[float, float]:
    """
    Computes visual typing diff density across plateau frames within [start_t, end_t].
    Returns (normalized_score, raw_density_per_min).
    """
    dur = max(1.0, end_t - start_t)
    span_diffs = [d for d in diff_events if start_t <= d.timestamp <= end_t]

    if not span_diffs:
        return 0.0, 0.0

    # Diffs during typing or stabilized plateau moments
    plateau_diffs = [d for d in span_diffs if d.is_plateau]
    total_magnitude = sum(d.diff_magnitude for d in span_diffs)
    plateau_magnitude = sum(d.diff_magnitude for d in plateau_diffs)

    # Combined typing activity: micro diffs + plateau stabilization
    weighted_diff = total_magnitude + (0.5 * plateau_magnitude)
    density_per_min = (weighted_diff / dur) * 60.0

    # Normalization: typical code typing creates ~1.0-4.0 diff units per minute
    norm_density = min(1.0, density_per_min / 4.0)
    return round(norm_density, 4), round(density_per_min, 4)


class ClosedThoughtClipper:
    """
    multimodal highlight discovery engine implementing the Pedagogical Triad:
    S_triad = w1 * RMS_audio + w2 * Diff_visual + w3 * Tech_density + w4 * Bug2Fix_bonus - w5 * Penalty_deictic
    """

    def __init__(
        self,
        patterns_path: Optional[Path] = None,
        bandit: Optional[PedagogyScoreBandit] = None,
    ):
        self.bandit = bandit

        # Dangling Hinglish & English deictic pronouns
        self.deictic_starters = [
            "isko", "iska", "iski", "unko", "inka", "inhe",
            "ye wala", "yeh wala", "ye jo", "yeh jo", "woh wala", "wo wala",
            "this", "therefore", "it", "these", "those", "hence",
            "and then this", "and this", "because of that", "uske baad", "toh isko", "to isko", "aur ye",
        ]
        self.intro_hooks = [
            "why does", "kyun", "kaise", "what is", "kya hota hai", "problem ye hai",
            "the issue is", "dekho jab", "how to", "difference between", "let's understand",
            "notice what happens", "here is why", "understand how"
        ]
        self.resolution_markers = [
            "toh is tarah", "hence", "therefore", "ab dekho output", "now see the output",
            "compiled successfully", "error resolved", "so that is why", "and it works",
            "zero leaks", "assertion passed", "test passed", "output is"
        ]

        self._load_patterns(patterns_path or (settings.DATA_DIR / "hinglish_patterns.json"))

        # Scoring Weights (Configurable via Feedback Bandit or set_weights)
        if self.bandit:
            self.w_prosody = self.bandit.w1
            self.w_visual = self.bandit.w2
            self.w_tech = self.bandit.w3
            self.w_triad = self.bandit.w4
            self.w_deictic = self.bandit.w5
        else:
            self.w_prosody = 0.15   # w1
            self.w_visual = 0.25    # w2
            self.w_tech = 0.25      # w3
            self.w_triad = 0.35     # w4
            self.w_deictic = 2.0    # w5

    @property
    def w1(self) -> float:
        return self.w_prosody

    @property
    def w2(self) -> float:
        return self.w_visual

    @property
    def w3(self) -> float:
        return self.w_tech

    @property
    def w4(self) -> float:
        return self.w_triad

    @property
    def w5(self) -> float:
        return self.w_deictic

    def set_weights(self, weights: Dict[str, float]):
        """Updates internal highlight weights."""
        if "w1" in weights:
            self.w_prosody = weights["w1"]
        elif "w_prosody" in weights:
            self.w_prosody = weights["w_prosody"]

        if "w2" in weights:
            self.w_visual = weights["w2"]
        elif "w_visual" in weights:
            self.w_visual = weights["w_visual"]

        if "w3" in weights:
            self.w_tech = weights["w3"]
        elif "w_tech" in weights:
            self.w_tech = weights["w_tech"]

        if "w4" in weights:
            self.w_triad = weights["w4"]
        elif "w_triad" in weights:
            self.w_triad = weights["w_triad"]

        if "w5" in weights:
            self.w_deictic = weights["w5"]
        elif "w_deictic" in weights:
            self.w_deictic = weights["w_deictic"]

    def _load_patterns(self, path: Path):
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    extra_deictic = data.get("deictic_penalized_starters", [])
                    for d in extra_deictic:
                        if d not in self.deictic_starters:
                            self.deictic_starters.append(d)
                    self.intro_hooks = data.get("triad_intro_hooks", self.intro_hooks)
                    self.resolution_markers = data.get("triad_resolution_markers", self.resolution_markers)
            except Exception:
                pass

    def find_sentence_boundaries(
        self,
        words: List[WordAlignment],
        pause_threshold: float = 0.40,
    ) -> List[int]:
        """
        Locates sentence boundaries based on punctuation (. ? ! ।) or natural audio pauses (>= 0.4s).
        Returns a list of word indices where a new sentence/clause starts.
        """
        if not words:
            return []

        boundaries: List[int] = [0]
        for idx in range(len(words) - 1):
            curr_w = words[idx]
            next_w = words[idx + 1]
            pause = next_w.start - curr_w.end
            has_punct = bool(re.search(r"[\.\?!।]", curr_w.word))
            if has_punct or pause >= pause_threshold:
                boundaries.append(idx + 1)

        if boundaries[-1] != len(words):
            boundaries.append(len(words))
        return boundaries

    def magnetically_snap_window(
        self,
        target_start: float,
        target_end: float,
        words: List[WordAlignment],
        min_duration: float = 30.0,
        max_duration: float = 60.0,
        pause_threshold: float = 0.40,
    ) -> Tuple[float, float, int, int]:
        """
        Magnetically snaps candidate clip start and end boundaries to complete sentences
        and natural audio pauses (>= 0.4s) strictly between min_duration (30s) and max_duration (60s).
        """
        if not words:
            return target_start, target_end, 0, 0

        boundaries = self.find_sentence_boundaries(words, pause_threshold=pause_threshold)
        boundary_times = [
            (b_idx, words[b_idx].start if b_idx < len(words) else words[-1].end)
            for b_idx in boundaries
        ]

        # Find closest start boundary
        best_start_idx = 0
        best_start_t = words[0].start
        min_start_diff = float("inf")
        for b_idx, t in boundary_times:
            if abs(t - target_start) < min_start_diff:
                min_start_diff = abs(t - target_start)
                best_start_idx = b_idx
                best_start_t = t

        # Find best end boundary strictly satisfying 30s <= dur <= 60s
        best_end_idx = len(words) - 1
        best_end_t = words[-1].end
        min_end_diff = float("inf")

        valid_found = False
        for b_idx in boundaries:
            if b_idx <= best_start_idx:
                continue
            end_word_idx = b_idx - 1
            if end_word_idx < 0 or end_word_idx >= len(words):
                continue
            t = words[end_word_idx].end
            dur = t - best_start_t
            if min_duration <= dur <= max_duration:
                diff = abs(t - target_end)
                if diff < min_end_diff:
                    min_end_diff = diff
                    best_end_idx = end_word_idx
                    best_end_t = t
                    valid_found = True

        if not valid_found:
            # Fallback: scan words to find closest complete word end satisfying [min_duration, max_duration]
            clamped_dur = min(max_duration, max(min_duration, target_end - best_start_t))
            target_t = best_start_t + clamped_dur
            best_diff = float("inf")
            for idx in range(best_start_idx, len(words)):
                dur = words[idx].end - best_start_t
                if min_duration <= dur <= max_duration:
                    diff = abs(words[idx].end - target_t)
                    if diff < best_diff:
                        best_diff = diff
                        best_end_idx = idx
                        best_end_t = words[idx].end

        return round(best_start_t, 2), round(best_end_t, 2), best_start_idx, best_end_idx

    def extract_highlights(
        self,
        words: List[WordAlignment],
        diff_events: List[VisualDiffEvent],
        min_duration: float = 30.0,
        max_duration: float = 60.0,
        top_k: int = 3,
        audio_source: Optional[Union[str, Path, np.ndarray]] = None,
    ) -> List[CandidateSpan]:
        """
        Evaluates candidate windows and extracts top-ranked complete-thought clips.
        Magnetically snaps start and end boundaries to sentence ends and pauses (>= 0.4s)
        strictly between 30s and 60s.
        """
        if not words:
            return []

        # Update weights from bandit if connected
        if self.bandit:
            self.set_weights(self.bandit.get_weights())

        sentence_boundaries = self.find_sentence_boundaries(words, pause_threshold=0.40)
        candidates: List[CandidateSpan] = []
        num_bounds = len(sentence_boundaries)

        # Iterate over pairs of magnetically snapped sentence/pause boundaries
        for i in range(num_bounds - 1):
            start_word_idx = sentence_boundaries[i]
            if start_word_idx >= len(words):
                continue
            start_t = words[start_word_idx].start

            for j in range(i + 1, num_bounds):
                end_word_idx = sentence_boundaries[j] - 1
                if end_word_idx >= len(words):
                    end_word_idx = len(words) - 1
                end_t = words[end_word_idx].end
                dur = end_t - start_t

                # Strict duration window: 30s to 60s
                if min_duration <= dur <= max_duration:
                    span_words = words[start_word_idx : end_word_idx + 1]
                    (
                        score,
                        deictic_flag,
                        tech_dens,
                        feat_dict,
                        rms_val,
                        vis_val,
                    ) = self._score_span(
                        span_words, start_t, end_t, diff_events, audio_source=audio_source
                    )

                    first_phrase = " ".join(w.word for w in span_words[:4])
                    last_phrase = " ".join(w.word for w in span_words[-4:])

                    cand = CandidateSpan(
                        start_index=start_word_idx,
                        end_index=end_word_idx,
                        start_time=round(start_t, 2),
                        end_time=round(end_t, 2),
                        triad_score=round(score, 3),
                        tech_density=round(tech_dens, 2),
                        deictic_penalized=deictic_flag,
                        first_phrase=first_phrase,
                        last_phrase=last_phrase,
                        features=feat_dict,
                        audio_rms=rms_val,
                        visual_density=vis_val,
                    )
                    candidates.append(cand)

        # Sort by triad score descending
        candidates.sort(key=lambda c: c.triad_score, reverse=True)

        # Non-maximum suppression (prevent overlapping candidate clips)
        selected: List[CandidateSpan] = []
        for cand in candidates:
            overlap = False
            for sel in selected:
                if not (cand.end_time <= sel.start_time or cand.start_time >= sel.end_time):
                    overlap = True
                    break
            if not overlap:
                selected.append(cand)
            if len(selected) >= top_k:
                break

        # Fallback if no strict boundary pair matched: magnetically snap first available window
        if not selected and words:
            total_dur = words[-1].end - words[0].start
            target_end_t = words[0].start + min(max_duration, max(min_duration, total_dur))
            s_t, e_t, s_idx, e_idx = self.magnetically_snap_window(
                words[0].start, target_end_t, words, min_duration, max_duration, pause_threshold=0.40
            )
            span_words = words[s_idx : e_idx + 1] if e_idx >= s_idx else words
            (
                fallback_score,
                deictic_flag,
                tech_dens,
                feat_dict,
                rms_val,
                vis_val,
            ) = self._score_span(span_words, s_t, e_t, diff_events, audio_source=audio_source)

            selected.append(
                CandidateSpan(
                    start_index=s_idx,
                    end_index=e_idx,
                    start_time=round(s_t, 2),
                    end_time=round(e_t, 2),
                    triad_score=round(fallback_score, 3),
                    tech_density=round(tech_dens, 2),
                    deictic_penalized=deictic_flag,
                    first_phrase=" ".join(w.word for w in span_words[:4]),
                    last_phrase=" ".join(w.word for w in span_words[-4:]),
                    features=feat_dict,
                    audio_rms=rms_val,
                    visual_density=vis_val,
                )
            )

        return selected

    def _score_span(
        self,
        span_words: List[WordAlignment],
        start_t: float,
        end_t: float,
        diff_events: List[VisualDiffEvent],
        audio_source: Optional[Union[str, Path, np.ndarray]] = None,
    ) -> Tuple[float, bool, float, Dict[str, float], float, float]:
        dur = max(1.0, end_t - start_t)

        # 1. Real Vocal Energy RMS via numpy/scipy
        if audio_source is not None:
            norm_rms = compute_audio_rms(audio_source, start_t, end_t)
        else:
            # Estimate prosodic energy baseline from confidence if audio file omitted
            norm_rms = min(1.0, np.mean([w.confidence for w in span_words]) * 0.7) if span_words else 0.5

        # 2. Visual Typing Diff Density across plateau frames
        norm_visual, raw_vis_density = compute_visual_typing_density(diff_events, start_t, end_t)

        # 3. Technical Term Density (Terms per minute)
        tech_count = sum(1 for w in span_words if w.is_technical)
        tech_density_pm = (tech_count / dur) * 60.0
        norm_tech = min(1.0, tech_density_pm / 6.0)

        # 4. Deictic Entry Penalty (First 3 seconds check)
        # Enforce on dangling Hinglish/English pronouns: 'isko', 'ye wala', 'this', 'therefore'
        deictic_penalized = False
        first_3s_words = [w for w in span_words if (w.start - start_t) <= 3.0]
        first_3s_text = " ".join(w.word for w in first_3s_words).lower()

        # Check start of the clip or opening clause
        for starter in self.deictic_starters:
            pattern = rf"\b{re.escape(starter)}\b"
            match = re.search(pattern, first_3s_text)
            if match:
                # If it occurs in the opening 2 words or starts the clip without prior noun context
                token_index = first_3s_text[:match.start()].count(" ")
                if token_index <= 2:
                    deictic_penalized = True
                    break

        # 5. Triad / Bug-to-Fix Bonus (Hook in Q1, Mutation in Q2-Q3, Resolution in Q4)
        triad_bonus = 0.0
        q1_words = " ".join(w.word for w in span_words[: max(1, len(span_words) // 4)]).lower()
        q4_words = " ".join(w.word for w in span_words[len(span_words) * 3 // 4 :]).lower()

        has_hook = any(hook in q1_words for hook in self.intro_hooks)
        has_resolution = any(res in q4_words for res in self.resolution_markers)

        # Visual diffs or code mutation in middle half
        mid_start = start_t + (dur * 0.25)
        mid_end = start_t + (dur * 0.75)
        mid_diffs = sum(1 for d in diff_events if mid_start <= d.timestamp <= mid_end and d.is_plateau)
        has_mutation = mid_diffs >= 1

        if has_hook:
            triad_bonus += 0.40
        if has_mutation:
            triad_bonus += 0.30
        if has_resolution:
            triad_bonus += 0.30

        penalty_deictic_val = 1.0 if deictic_penalized else 0.0

        # Formula: S_triad = w1*RMS + w2*Diff + w3*Tech + w4*Bug2Fix - w5*Penalty_deictic
        score = (
            (self.w_prosody * norm_rms)
            + (self.w_visual * norm_visual)
            + (self.w_tech * norm_tech)
            + (self.w_triad * triad_bonus)
            - (self.w_deictic * penalty_deictic_val)
        )

        features = {
            "rms_audio": round(float(norm_rms), 4),
            "diff_visual": round(float(norm_visual), 4),
            "tech_density": round(float(norm_tech), 4),
            "bug2fix_bonus": round(float(triad_bonus), 4),
            "penalty_deictic": round(float(penalty_deictic_val), 4),
        }

        return max(0.1, round(score, 4)), deictic_penalized, tech_density_pm, features, norm_rms, norm_visual
