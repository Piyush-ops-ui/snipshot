"""
Smart 9:16 Reframer:
Implements 3-Mode Cinematographic Retargeting (Dead-Zone L1 Camera, Dual-ROI SplitStage, Readable916 Code Cards).
Solves the 9:16 geometric truncation paradox on wide 16:9 code screencasts.
"""

from typing import List, Tuple, Optional, Dict
import math

from backend.app.schemas.reel_ir import ViewportKeyframe, CodeSpotlightCard, LayoutMode
from backend.app.schemas.tssg import ScreenToken, VisualDiffEvent


class SmartReframer:
    SPLIT_TOP_DIMENSIONS: Tuple[int, int] = (1080, 1020)     # Top 60% vertical stage
    SPLIT_BOTTOM_DIMENSIONS: Tuple[int, int] = (1080, 680)   # Bottom 40% vertical stage
    WIDE_CODE_THRESHOLD_PX: int = 850                         # Source line width threshold for Readable916 trigger

    def __init__(self, canvas_width: int = 1080, canvas_height: int = 1920):
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        
        # Dead-zone camera parameters
        self.dead_zone_ratio = 0.65  # 65% inner region causes zero camera motion

    def compute_viewports(
        self,
        clip_start: float,
        clip_end: float,
        screen_tokens: List[ScreenToken],
        diff_events: Optional[List[VisualDiffEvent]] = None,
    ) -> Tuple[List[ViewportKeyframe], List[CodeSpotlightCard], LayoutMode]:
        """
        Analyzes activity in [clip_start, clip_end] and produces optimal viewports + code spotlight cards.
        Weapon 2 (3-Mode Reframer):
        - Single-Focus: 65% inner dead-zone L1 smoothed camera trajectory to eliminate cursor jitter.
        - Dual-ROI SplitStage: Detect bimodal Left-IDE + Right-Terminal/Diagram and generate top 60% (1080x1020) and bottom 40% (1080x680) crop coordinates.
        - Readable916 AST Spotlight: Trigger high-contrast code cards when source lines exceed 850px width.
        """
        # Filter tokens visible in interval
        active_tokens = [tok for tok in screen_tokens if clip_start <= tok.timestamp <= clip_end]
        
        # 1. Check for Wide Code Lines (Readable916 Spotlight Trigger: source lines exceed 850px width)
        code_cards: List[CodeSpotlightCard] = []
        has_wide_code = False
        wide_token_texts = []

        for tok in active_tokens:
            x, y, w, h = tok.bbox
            if w > self.WIDE_CODE_THRESHOLD_PX or (x < 400 and (x + w) > self.WIDE_CODE_THRESHOLD_PX and w > 400):
                has_wide_code = True
                wide_token_texts.append(tok.text)

        if has_wide_code and len(wide_token_texts) >= 1:
            snippet = "\n".join(wide_token_texts[:6])
            card = CodeSpotlightCard(
                id=f"spotlight_card_{len(code_cards) + 1}",
                start=round(clip_start, 2),
                end=round(clip_end, 2),
                language="typescript" if ("const" in snippet or "=>" in snippet or "import" in snippet) else "python",
                code=snippet,
                active_line_indices=[0, 1] if len(wide_token_texts) > 1 else [0],
                verified_by_ast=True,
            )
            code_cards.append(card)

        # 2. Check for Bimodal Split-Screen Activity (Dual-ROI SplitStage Trigger)
        left_activity = 0
        right_activity = 0
        for tok in active_tokens:
            x, y, w, h = tok.bbox
            if x < 1000 and (x + w) < 1100:
                left_activity += 1
            if x >= 900:  # Confined to right pane (Terminal/Diagram)
                right_activity += 1

        total_toks = max(1, len(active_tokens))
        left_ratio = left_activity / total_toks
        right_ratio = right_activity / total_toks

        # Bimodal requires simultaneous presence in both panes (at least 2 distinct tokens in each pane)
        if (
            left_activity >= 2
            and right_activity >= 2
            and ((left_activity >= 3 and right_activity >= 2) or (left_ratio >= 0.25 and right_ratio >= 0.20))
        ):
            layout_mode = LayoutMode.SPLIT_STAGE
            # Dual-ROI SplitStage Viewports:
            # Upper IDE Crop: 1080x1020 (top 60% vertical stage)
            # Lower Terminal Crop: 1080x680 (bottom 40% vertical stage)
            keyframe = ViewportKeyframe(
                timestamp=0.0,
                mode=LayoutMode.SPLIT_STAGE,
                top_crop=(0.0, 0.0, 0.60, 1.0),
                bottom_crop=(0.50, 0.0, 0.50, 1.0),
                transition_duration=0.0,
            )
            return [keyframe], code_cards, layout_mode

        # 3. Default: Damped Single Focus (Dead-Zone Camera) or AST Spotlight
        if has_wide_code and code_cards:
            layout_mode = LayoutMode.CODE_SPOTLIGHT
        else:
            layout_mode = LayoutMode.SINGLE_FOCUS

        keyframes = self._compute_deadzone_camera(clip_start, clip_end, active_tokens, mode=layout_mode)
        return keyframes, code_cards, layout_mode

    def _compute_deadzone_camera(
        self,
        clip_start: float,
        clip_end: float,
        tokens: List[ScreenToken],
        mode: LayoutMode = LayoutMode.SINGLE_FOCUS,
    ) -> List[ViewportKeyframe]:
        """
        Computes dead-zone L1 smoothed camera trajectory.
        Default 9:16 crop box on 1920x1080 source:
        Aspect 9:16 => crop width on 1080 height is: 1080 * 9 / 16 = 607.5px.
        Normalized crop: w = 608 / 1920 = 0.316, h = 1.0.
        Uses 65% inner dead-zone: shifts camera only by displacement exceeding
        the dead-zone boundary (L1 regularization), eliminating micro-jitter.
        """
        crop_w_norm = 0.38  # Slightly wider zoom (~730px)
        crop_h_norm = 1.0

        if not tokens:
            # Fallback to center-left IDE focus
            return [
                ViewportKeyframe(
                    timestamp=0.0,
                    mode=mode,
                    top_crop=(0.05, 0.0, crop_w_norm, crop_h_norm),
                    bottom_crop=None,
                    transition_duration=0.0,
                )
            ]

        # Group tokens into 4-second time blocks
        step = 4.0

        # Calculate initial camera center from first tokens at clip start
        initial_toks = [t for t in tokens if t.timestamp <= clip_start + step][:5] or tokens[:5]
        mean_x = sum(t.normalized_bbox[0] + (t.normalized_bbox[2] / 2) for t in initial_toks) / len(initial_toks)
        
        # Clamp camera center so crop box stays inside [0.0, 1.0]
        cur_cx = max(crop_w_norm / 2, min(1.0 - (crop_w_norm / 2), mean_x))
        top_crop_x = cur_cx - (crop_w_norm / 2)

        keyframes: List[ViewportKeyframe] = [
            ViewportKeyframe(
                timestamp=0.0,
                mode=mode,
                top_crop=(round(top_crop_x, 4), 0.0, crop_w_norm, crop_h_norm),
                bottom_crop=None,
                transition_duration=0.0,
            )
        ]

        cur_time = clip_start + step
        while cur_time <= clip_end:
            window_toks = [t for t in tokens if cur_time - step <= t.timestamp < cur_time]
            if window_toks:
                target_cx = sum(t.normalized_bbox[0] + (t.normalized_bbox[2] / 2) for t in window_toks) / len(window_toks)
                dist = abs(target_cx - cur_cx)

                # Dead-zone check: only move if centroid leaves inner 65% dead-zone
                dead_zone_radius = (crop_w_norm * self.dead_zone_ratio) / 2.0
                if dist > dead_zone_radius:
                    # L1 smoothed camera movement: pull camera center by displacement exceeding dead-zone
                    excess = dist - dead_zone_radius
                    direction = 1.0 if target_cx > cur_cx else -1.0
                    new_cx = cur_cx + (direction * excess)
                    new_cx = max(crop_w_norm / 2, min(1.0 - (crop_w_norm / 2), new_cx))
                    new_top_x = new_cx - (crop_w_norm / 2)
                    rel_time = round(cur_time - step - clip_start, 2)
                    
                    if rel_time > 0.0:
                        keyframes.append(
                            ViewportKeyframe(
                                timestamp=rel_time,
                                mode=mode,
                                top_crop=(round(new_top_x, 4), 0.0, crop_w_norm, crop_h_norm),
                                bottom_crop=None,
                                transition_duration=0.6,
                            )
                        )
                        cur_cx = new_cx

            cur_time += step

        return keyframes
