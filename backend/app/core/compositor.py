"""
High-Speed Pillow + Pygments + FFmpeg Frame Compositor.
Renders declarative Reel-IR timelines into 1080x1920 9:16 videos.
Streams raw in-memory frames directly into an FFmpeg subprocess pipe for sub-15s CPU renders.
"""

from typing import Optional, Callable, List, Tuple
import os
import subprocess
import gc
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
    PILLOW_AVAILABLE = True
except ImportError:
    Image = None
    ImageDraw = None
    ImageFont = None
    PILLOW_AVAILABLE = False

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    cv2 = None
    CV2_AVAILABLE = False

try:
    import qrcode
    QRCODE_AVAILABLE = True
except ImportError:
    qrcode = None
    QRCODE_AVAILABLE = False

from backend.app.schemas.reel_ir import (
    ReelIR,
    WordAlignment,
    LayoutMode,
    ViewportKeyframe,
    CodeSpotlightCard,
    TemplateArchetype,
    RedactionBox,
    SocialGrowthPack,
)
from backend.app.services.ffmpeg_service import FFmpegService
from backend.app.services.hardware_profiler import detect_hardware_profile
from backend.app.config import settings


def get_font(size: int = 24, monospace: bool = True) -> ImageFont.ImageFont:
    """Loads bundled or system TrueType font with graceful bitmap fallback."""
    if not PILLOW_AVAILABLE:
        return None
    font_candidates = [
        str(settings.FONTS_DIR / "JetBrainsMono-Bold.ttf"),
        str(settings.FONTS_DIR / "Inter-SemiBold.ttf"),
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf",
    ]
    for candidate in font_candidates:
        if os.path.exists(candidate):
            try:
                return ImageFont.truetype(candidate, size)
            except Exception:
                pass
    return ImageFont.load_default()


class ReelCompositor:
    def __init__(self, width: int = 1080, height: int = 1920, fps: int = 30):
        self.width = width
        self.height = height
        self.fps = fps
        self.ffmpeg = FFmpegService()

    def detect_silent_typing_gaps(
        self,
        transcript: List[WordAlignment],
        total_duration: float,
        min_gap_seconds: float = 1.2,
    ) -> List[Tuple[float, float]]:
        """
        Weapon 9: Detects silent intervals > 1.2s between spoken words where
        typing occurs without narration.
        """
        gaps: List[Tuple[float, float]] = []
        if not transcript:
            if total_duration > min_gap_seconds:
                gaps.append((0.0, round(total_duration, 2)))
            return gaps

        sorted_words = sorted(transcript, key=lambda w: w.start)

        # Gap before first word
        if sorted_words[0].start > min_gap_seconds:
            gaps.append((0.0, round(sorted_words[0].start, 2)))

        # Gaps between consecutive words
        for i in range(len(sorted_words) - 1):
            gap_start = sorted_words[i].end
            gap_end = sorted_words[i + 1].start
            if (gap_end - gap_start) > min_gap_seconds:
                gaps.append((round(gap_start, 2), round(gap_end, 2)))

        # Gap after last word
        if (total_duration - sorted_words[-1].end) > min_gap_seconds:
            gaps.append((round(sorted_words[-1].end, 2), round(total_duration, 2)))

        return gaps

    def render(
        self,
        reel: ReelIR,
        output_path: str,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> str:
        """
        Renders complete 1080x1920 Reel MP4 from ReelIR JSON document.
        Streams raw in-memory frames directly into an FFmpeg subprocess pipe.
        """
        if not PILLOW_AVAILABLE:
            raise RuntimeError("Pillow is required for video composition.")

        # Sequential memory guard
        gc.collect()

        total_duration = max(1.0, reel.total_duration)
        total_frames = int(total_duration * self.fps)
        hw_profile = detect_hardware_profile()

        # Weapon 9: Detect silent typing gaps > 1.2s if not pre-populated
        hyperlapse_intervals = list(reel.typing_hyperlapse_intervals)
        if not hyperlapse_intervals and reel.transcript:
            hyperlapse_intervals = self.detect_silent_typing_gaps(
                reel.transcript, total_duration, min_gap_seconds=1.2
            )
            reel.typing_hyperlapse_intervals = hyperlapse_intervals

        # Open FFmpeg subprocess taking raw RGBA frames on stdin
        proc = self.ffmpeg.open_pipe_renderer(
            output_mp4_path=output_path,
            audio_path=reel.audio_path,
            width=self.width,
            height=self.height,
            fps=self.fps,
            encoder=hw_profile.recommended_encoder,
        )

        cap = None
        if reel.source_media_path and os.path.exists(reel.source_media_path) and CV2_AVAILABLE:
            cap = cv2.VideoCapture(reel.source_media_path)

        # Pre-cache fonts
        title_font = get_font(34, monospace=False)
        caption_font = get_font(40, monospace=False)
        code_font = get_font(28, monospace=True)
        badge_font = get_font(22, monospace=True)

        source_offset = 0.0
        dt = 1.0 / self.fps

        try:
            for frame_idx in range(total_frames):
                rel_time = frame_idx / self.fps

                # Weapon 9: Check if current moment is inside hyperlapse interval
                in_hyperlapse = any(s <= rel_time <= e for s, e in hyperlapse_intervals)

                # Weapon 7: Freeze-frame check for PREDICT_OUTPUT archetype (2-second freeze callout)
                is_freeze = (
                    reel.template_archetype == TemplateArchetype.PREDICT_OUTPUT
                    and (total_duration - 4.0) <= rel_time <= (total_duration - 2.0)
                )

                if is_freeze:
                    # Video freezes on screen during pause callout
                    abs_time = reel.clip_start + max(0.0, total_duration - 4.0)
                else:
                    abs_time = reel.clip_start + source_offset

                # Advance source video time: 2.5x speed during silent typing hyperlapse
                if not is_freeze:
                    source_offset += dt * (2.5 if in_hyperlapse else 1.0)

                # 1. Base Canvas
                img = Image.new("RGBA", (self.width, self.height), color=reel.brand_kit.background_color)
                draw = ImageDraw.Draw(img)

                # 2. Viewport Video Rendering (with SafeCohort localized secret blur)
                active_keyframe = self._get_active_keyframe(reel.viewports, rel_time)
                if cap is not None and cap.isOpened():
                    self._render_video_layer(cap, draw, img, abs_time, active_keyframe, reel.redaction_boxes)
                else:
                    self._render_synthetic_ide_layer(draw, img, rel_time, active_keyframe, reel.redaction_boxes)

                # 3. Code Spotlight Card Layer or Archetype Layout
                if reel.template_archetype == TemplateArchetype.VS_BATTLE:
                    self._render_vs_battle_cards(draw, reel, rel_time, code_font)
                else:
                    active_card = self._get_active_code_card(reel.code_cards, rel_time)
                    if active_card:
                        self._render_code_card(draw, active_card, code_font, reel.brand_kit.primary_color)

                # 4. Captions & Karaoke Word Highlights
                active_words, active_kw = self._get_active_caption_context(reel.transcript, rel_time)
                self._render_karaoke_hud(
                    draw, active_words, active_kw, caption_font, badge_font, reel.brand_kit
                )

                # 5. Header Branding & Animated Bottom Progress Bar (with Archetype & Hyperlapse support)
                self._render_brand_elements(draw, reel, rel_time, abs_time, total_duration, title_font)

                # 6. Predict Output Freeze Callout (Weapon 7 Archetype)
                if is_freeze:
                    self._render_predict_output_callout(draw)

                # 7. Outro QR Bumper (Weapon 8 Screen-Grounded Growth Pack)
                if reel.brand_kit.enable_outro_bumper and rel_time >= (total_duration - reel.brand_kit.outro_bumper_duration):
                    self._render_outro_qr_bumper(draw, img, reel, rel_time, total_duration, title_font)

                # Write RGBA frame to FFmpeg stdin
                proc.stdin.write(img.tobytes())

                # Periodic progress callback
                if progress_callback and frame_idx % 15 == 0:
                    pct = round((frame_idx / total_frames) * 100.0, 1)
                    progress_callback(pct)

            proc.stdin.close()
            proc.wait()

        finally:
            if cap is not None:
                cap.release()

        if progress_callback:
            progress_callback(100.0)

        return output_path

    def _get_active_keyframe(self, keyframes: List[ViewportKeyframe], rel_time: float) -> ViewportKeyframe:
        if not keyframes:
            return ViewportKeyframe(
                timestamp=0.0,
                mode=LayoutMode.SINGLE_FOCUS,
                top_crop=(0.0, 0.0, 0.5, 1.0),
            )
        active = keyframes[0]
        for kf in keyframes:
            if kf.timestamp <= rel_time:
                active = kf
            else:
                break
        return active

    def _get_active_code_card(self, cards: List[CodeSpotlightCard], rel_time: float) -> Optional[CodeSpotlightCard]:
        for card in cards:
            if card.start <= rel_time <= card.end:
                return card
        return None

    def _get_active_caption_context(
        self, transcript: List[WordAlignment], rel_time: float
    ) -> Tuple[List[WordAlignment], Optional[WordAlignment]]:
        # Find active word
        active_word = None
        for w in transcript:
            if w.start <= rel_time <= w.end:
                active_word = w
                break

        # Show current phrase (window of ~6 words surrounding current time)
        window = [w for w in transcript if (rel_time - 1.8) <= w.start <= (rel_time + 1.8)]
        if not window and transcript:
            # Fallback to closest word
            closest = min(transcript, key=lambda w: abs(w.start - rel_time))
            window = [closest]

        return window, active_word

    def _apply_safe_cohort_blur(
        self, frame_bgr, redaction_boxes: List[RedactionBox], abs_time: float
    ):
        """Applies localized Gaussian blur over any secret/PII bounding boxes visible at abs_time (Weapon 5)."""
        if not CV2_AVAILABLE or cv2 is None or frame_bgr is None or not redaction_boxes:
            return frame_bgr
        h_src, w_src = frame_bgr.shape[:2]
        for rbox in redaction_boxes:
            if rbox.start <= abs_time <= rbox.end:
                rx, ry, rw, rh = int(rbox.box[0]), int(rbox.box[1]), int(rbox.box[2]), int(rbox.box[3])
                rx = max(0, min(w_src - 1, rx))
                ry = max(0, min(h_src - 1, ry))
                rw = max(1, min(w_src - rx, rw))
                rh = max(1, min(h_src - ry, rh))
                
                pad = 25
                y0 = max(0, ry - pad)
                y1 = min(h_src, ry + rh + pad)
                x0 = max(0, rx - pad)
                x1 = min(w_src, rx + rw + pad)
                
                padded_roi = frame_bgr[y0:y1, x0:x1]
                if padded_roi.size > 0:
                    blurred_padded = cv2.GaussianBlur(padded_roi, (51, 51), 0)
                    frame_bgr[ry : ry + rh, rx : rx + rw] = blurred_padded[
                        ry - y0 : ry - y0 + rh, rx - x0 : rx - x0 + rw
                    ]
        return frame_bgr

    def _render_video_layer(
        self, cap, draw, img, abs_time: float, keyframe: ViewportKeyframe, redaction_boxes: List[RedactionBox]
    ):
        """Extracts source frame, applies SafeCohort blur, and crops according to ViewportKeyframe."""
        if not CV2_AVAILABLE:
            return
        cap.set(cv2.CAP_PROP_POS_MSEC, abs_time * 1000.0)
        ret, frame_bgr = cap.read()
        if not ret or frame_bgr is None:
            return

        # Weapon 5: SafeCohort Secret & PII Blur Shield
        frame_bgr = self._apply_safe_cohort_blur(frame_bgr, redaction_boxes, abs_time)

        h_src, w_src = frame_bgr.shape[:2]

        if keyframe.mode == LayoutMode.SPLIT_STAGE and keyframe.bottom_crop:
            # Upper IDE Crop: 1080x1020 (top 60% viewport)
            tx, ty, tw, th = keyframe.top_crop
            crop_top_bgr = frame_bgr[int(ty * h_src) : int((ty + th) * h_src), int(tx * w_src) : int((tx + tw) * w_src)]
            if crop_top_bgr.size > 0:
                crop_top_rgb = cv2.cvtColor(crop_top_bgr, cv2.COLOR_BGR2RGB)
                pil_top = Image.fromarray(crop_top_rgb).resize((self.width, 1020), Image.Resampling.BILINEAR)
                img.paste(pil_top, (0, 120))

            # Lower Terminal Crop: 1080x680 (bottom 40% viewport)
            bx, by, bw, bh = keyframe.bottom_crop
            crop_bot_bgr = frame_bgr[int(by * h_src) : int((by + bh) * h_src), int(bx * w_src) : int((bx + bw) * w_src)]
            if crop_bot_bgr.size > 0:
                crop_bot_rgb = cv2.cvtColor(crop_bot_bgr, cv2.COLOR_BGR2RGB)
                pil_bot = Image.fromarray(crop_bot_rgb).resize((self.width, 680), Image.Resampling.BILINEAR)
                img.paste(pil_bot, (0, 1160))

            # Split divider line
            draw.line([(0, 1150), (self.width, 1150)], fill="#38BDF8", width=3)
        else:
            # Single Focus Crop: Scaled to 1080x1440
            tx, ty, tw, th = keyframe.top_crop
            x0 = int(tx * w_src)
            y0 = int(ty * h_src)
            x1 = min(w_src, int((tx + tw) * w_src))
            y1 = min(h_src, int((ty + th) * h_src))
            crop_bgr = frame_bgr[y0:y1, x0:x1]
            if crop_bgr.size > 0:
                crop_rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
                pil_crop = Image.fromarray(crop_rgb).resize((self.width, 1440), Image.Resampling.BILINEAR)
                img.paste(pil_crop, (0, 120))

    def _render_synthetic_ide_layer(
        self, draw, img, rel_time: float, keyframe: ViewportKeyframe, redaction_boxes: List[RedactionBox]
    ):
        """High-tech synthetic terminal & editor canvas for Mode B explainers."""
        # Top Editor Box
        draw.rounded_rectangle([(30, 140), (self.width - 30, 1080)], radius=16, fill="#1E293B", outline="#334155", width=2)
        # Window buttons (macOS style)
        draw.ellipse([(60, 165), (76, 181)], fill="#EF4444")
        draw.ellipse([(90, 165), (106, 181)], fill="#F59E0B")
        draw.ellipse([(120, 165), (136, 181)], fill="#10B981")

        # Bottom Terminal Box
        draw.rounded_rectangle([(30, 1120), (self.width - 30, 1540)], radius=16, fill="#0F172A", outline="#1E293B", width=2)
        draw.text((60, 1140), "> terminal -- active execution", fill="#64748B", font=get_font(20, monospace=True))

        # If synthetic secret redacted
        for rbox in redaction_boxes:
            if rbox.start <= rel_time <= rbox.end:
                draw.rounded_rectangle([(100, 360), (self.width - 100, 440)], radius=10, fill="#0F172A", outline="#EF4444", width=2)
                draw.text((120, 385), f"[SAFECALL BLUR: {rbox.secret_type.upper()}]", fill="#EF4444", font=get_font(22, True))

    def _render_code_card(self, draw, card: CodeSpotlightCard, font, accent_color: str):
        """Renders high-contrast AST Code Spotlight Card in upper viewport."""
        card_rect = [(40, 220), (self.width - 40, 780)]
        draw.rounded_rectangle(card_rect, radius=18, fill="#090D16", outline=accent_color, width=3)
        
        # Header tab
        draw.rounded_rectangle([(40, 220), (320, 265)], radius=12, fill="#1E293B")
        draw.text((60, 230), f"AST-VERIFIED: {card.language.upper()}", fill=accent_color, font=get_font(18, True))

        # Render code lines with syntax colors
        lines = card.code.split("\n")
        y = 290
        for idx, line in enumerate(lines[:12]):
            line_color = "#F8FAFC"
            if idx in card.active_line_indices:
                line_color = "#38BDF8"
                # Highlight bar
                draw.rectangle([(50, y - 2), (self.width - 50, y + 32)], fill="#1E293B")

            # Basic keyword coloring
            draw.text((60, y), f"{idx + 1:2d}  ", fill="#475569", font=font)
            draw.text((120, y), line[:42], fill=line_color, font=font)
            y += 38

    def _render_karaoke_hud(
        self, draw, words: List[WordAlignment], active_word: Optional[WordAlignment],
        font, badge_font, brand_kit
    ):
        """Renders dynamic karaoke caption box in the lower canvas."""
        hud_top = 1600
        hud_rect = [(40, hud_top), (self.width - 40, 1840)]
        draw.rounded_rectangle(hud_rect, radius=20, fill="#0F172A", outline="#1E293B", width=2)

        # Provenance Badge Indicator if active word was repaired
        if active_word and active_word.is_technical and brand_kit.show_provenance_badge:
            prov_text = f"SCREEN PROVENANCE: {active_word.word}"
            draw.rounded_rectangle([(70, hud_top - 40), (450, hud_top - 6)], radius=10, fill="#0284C7")
            draw.text((85, hud_top - 36), prov_text, fill="#FFFFFF", font=badge_font)

        # Words Layout
        full_text = " ".join(w.word for w in words)
        draw.text((70, hud_top + 30), full_text[:80], fill="#94A3B8", font=font)

        if active_word:
            # Highlight active word in cyan
            draw.text((70, hud_top + 95), f">> {active_word.word} <<", fill=brand_kit.primary_color, font=font)

    def _render_vs_battle_cards(self, draw, reel: ReelIR, rel_time: float, code_font):
        """
        Renders Weapon 7: VS Battle dual card comparison layout.
        Card 1: ❌ Legacy / Verbose
        Card 2: ✅ Modern / Optimal
        Separated by a glowing VS badge.
        """
        card_w = self.width - 80  # 1000px
        left_x = 40
        right_x = left_x + card_w

        # Determine snippets for Legacy vs Modern
        legacy_lines: List[str] = []
        modern_lines: List[str] = []

        if len(reel.code_cards) >= 2:
            legacy_lines = reel.code_cards[0].code.strip().split("\n")
            modern_lines = reel.code_cards[1].code.strip().split("\n")
        elif len(reel.code_cards) == 1:
            all_lines = reel.code_cards[0].code.strip().split("\n")
            split_idx = -1
            for idx, line in enumerate(all_lines):
                if any(delim in line.lower() for delim in ["vs", "modern", "optimal", "refactor", "---"]):
                    split_idx = idx
                    break
            if split_idx > 0:
                legacy_lines = all_lines[:split_idx]
                modern_lines = all_lines[split_idx:]
            else:
                mid = max(1, len(all_lines) // 2)
                legacy_lines = all_lines[:mid]
                modern_lines = all_lines[mid:]
        else:
            legacy_lines = [
                "// ❌ Legacy / Verbose",
                "const list = [];",
                "for (let i = 0; i < data.length; i++) {",
                "  if (data[i].valid) {",
                "    list.push(data[i].val * 2);",
                "  }",
                "}",
            ]
            modern_lines = [
                "// ✅ Modern / Optimal",
                "const list = data",
                "  .filter(d => d.valid)",
                "  .map(d => d.val * 2);",
            ]

        # Top Card: ❌ Legacy / Verbose
        top_y1, top_y2 = 140, 710
        draw.rounded_rectangle([(left_x, top_y1), (right_x, top_y2)], radius=18, fill="#180D14", outline="#EF4444", width=3)
        draw.rounded_rectangle([(left_x, top_y1), (left_x + 360, top_y1 + 45)], radius=12, fill="#7F1D1D")
        draw.text((left_x + 20, top_y1 + 10), "❌ Legacy / Verbose", fill="#FEE2E2", font=get_font(20, True))

        cy = top_y1 + 65
        for idx, line in enumerate(legacy_lines[:11]):
            draw.text((left_x + 20, cy), f"{idx + 1:2d} ", fill="#6B7280", font=code_font)
            draw.text((left_x + 75, cy), line[:38], fill="#FCA5A5", font=code_font)
            cy += 36

        # Middle VS Pill Badge
        badge_cx = self.width // 2
        badge_cy = 745
        draw.rounded_rectangle([(badge_cx - 85, badge_cy - 22), (badge_cx + 85, badge_cy + 22)], radius=22, fill="#3B0764", outline="#C084FC", width=3)
        draw.text((badge_cx - 58, badge_cy - 12), "⚡ VS ⚡", fill="#F5D0FE", font=get_font(20, True))

        # Bottom Card: ✅ Modern / Optimal
        bot_y1, bot_y2 = 780, 1350
        draw.rounded_rectangle([(left_x, bot_y1), (right_x, bot_y2)], radius=18, fill="#061C14", outline="#10B981", width=3)
        draw.rounded_rectangle([(left_x, bot_y1), (left_x + 360, bot_y1 + 45)], radius=12, fill="#064E3B")
        draw.text((left_x + 20, bot_y1 + 10), "✅ Modern / Optimal", fill="#D1FAE5", font=get_font(20, True))

        cy = bot_y1 + 65
        for idx, line in enumerate(modern_lines[:11]):
            draw.text((left_x + 20, cy), f"{idx + 1:2d} ", fill="#6B7280", font=code_font)
            draw.text((left_x + 75, cy), line[:38], fill="#6EE7B7", font=code_font)
            cy += 36

    def _render_brand_elements(
        self, draw, reel: ReelIR, rel_time: float, abs_time: float, total_duration: float, title_font
    ):
        """Renders header branding with Archetype styling and bottom progress indicator."""
        header_bg = "#0B0F19"
        status_label = "SNIPSHOT 9:16"
        status_color = reel.brand_kit.primary_color

        # Weapon 7: Pedagogical Archetype Templates
        if reel.template_archetype == TemplateArchetype.BUG_HUNTER:
            # Header starts Crimson Red and transitions to Emerald Green at error resolution
            if reel.error_resolved_at is not None:
                resolved_time = (
                    (reel.clip_start + reel.error_resolved_at)
                    if reel.error_resolved_at < reel.clip_start
                    else reel.error_resolved_at
                )
                is_resolved = abs_time >= resolved_time
            else:
                is_resolved = False

            if is_resolved:
                header_bg = "#064E3B"       # Dark Emerald
                status_label = "BUG RESOLVED [200 OK]"
                status_color = "#34D399"     # Emerald Green
            else:
                header_bg = "#7F1D1D"       # Dark Crimson
                status_label = "BUG HUNTER [FAILING]"
                status_color = "#F87171"     # Light Crimson
        elif reel.template_archetype == TemplateArchetype.VS_BATTLE:
            header_bg = "#3B0764"           # Deep Violet
            status_label = "VS BATTLE: LEGACY vs OPTIMAL"
            status_color = "#C084FC"
        elif reel.template_archetype == TemplateArchetype.PREDICT_OUTPUT:
            header_bg = "#78350F"           # Dark Amber
            status_label = "PREDICT THE OUTPUT ⏸️"
            status_color = "#FBBF24"
        else:
            header_bg = "#0B0F19"
            status_label = "SNIPSHOT 9:16"
            status_color = reel.brand_kit.primary_color

        # Header banner rectangle
        draw.rectangle([(0, 0), (self.width, 100)], fill=header_bg)
        brand_name = reel.brand_kit.watermark_text or "TechSummitTrainers"
        draw.text((40, 30), brand_name.upper(), fill="#F8FAFC", font=title_font)
        draw.text((self.width - 320, 35), status_label, fill=status_color, font=get_font(20, True))

        # Weapon 9: Dead-Air 2.5x Typing Hyperlapse Badge
        in_hyperlapse = any(s <= rel_time <= e for s, e in reel.typing_hyperlapse_intervals)
        if in_hyperlapse:
            draw.rounded_rectangle([(self.width - 350, 110), (self.width - 40, 155)], radius=10, fill="#0F172A", outline="#00F2FE", width=2)
            draw.text((self.width - 335, 122), "⚡ 2.5x HYPERLAPSE", fill="#00F2FE", font=get_font(18, True))

        # Bottom Progress Bar
        progress_ratio = min(1.0, rel_time / total_duration)
        bar_w = int(self.width * progress_ratio)
        draw.rectangle([(0, self.height - 14), (self.width, self.height)], fill="#1E293B")
        draw.rectangle([(0, self.height - 14), (bar_w, self.height)], fill=status_color)

    def _render_predict_output_callout(self, draw):
        """Renders 2-second freeze-frame callout banner for Predict Output archetype."""
        callout_rect = [(80, 800), (self.width - 80, 1020)]
        draw.rounded_rectangle(callout_rect, radius=24, fill="#78350F", outline="#FBBF24", width=4)
        draw.text((140, 835), "⏸️ PAUSE & COMMENT OUTPUT!", fill="#FEF3C7", font=get_font(38, False))
        draw.text((160, 915), "Can you predict what the console prints?", fill="#FDE68A", font=get_font(24, False))

    def _render_outro_qr_bumper(
        self, draw, img, reel: ReelIR, rel_time: float, total_duration: float, title_font
    ):
        """Renders branded outro bumper card with offline Scan-to-Copy-Code QR code (Weapon 8)."""
        card_rect = [(80, 420), (self.width - 80, 1460)]
        draw.rounded_rectangle(card_rect, radius=24, fill="#0B0F19", outline=reel.brand_kit.primary_color, width=3)

        brand_name = reel.brand_kit.name or "TechSummitTrainers"
        draw.text((120, 460), brand_name.upper(), fill="#F8FAFC", font=title_font)
        draw.text((120, 520), "SCAN TO COPY CODE SNIPPET", fill=reel.brand_kit.primary_color, font=get_font(30, False))

        # QR Code Generation via qrcode library
        qr_data = None
        if reel.social_growth_pack and reel.social_growth_pack.qr_code_data:
            qr_data = reel.social_growth_pack.qr_code_data
        elif reel.code_cards:
            qr_data = reel.code_cards[0].code
        elif reel.social_growth_pack and reel.social_growth_pack.pinned_code_comment:
            qr_data = reel.social_growth_pack.pinned_code_comment
        else:
            qr_data = "https://github.com/techsummit/snipshot"

        if QRCODE_AVAILABLE and qrcode is not None and qr_data:
            try:
                qr = qrcode.QRCode(
                    version=None,
                    error_correction=qrcode.constants.ERROR_CORRECT_M,
                    box_size=8,
                    border=2,
                )
                qr.add_data(qr_data)
                qr.make(fit=True)
                qr_pil = qr.make_image(fill_color="#0F172A", back_color="#FFFFFF").convert("RGBA")
                qr_pil = qr_pil.resize((360, 360), Image.Resampling.NEAREST)
                img.paste(qr_pil, ((self.width - 360) // 2, 600))
            except Exception:
                pass

        # Social Hashtags & Pinned Code Preview
        if reel.social_growth_pack:
            tags = " ".join(
                reel.social_growth_pack.stack_hashtags[:2] + reel.social_growth_pack.micro_api_hashtags[:2]
            )
            if tags:
                draw.text((120, 1020), tags, fill="#38BDF8", font=get_font(24, True))
            if reel.social_growth_pack.hook_title:
                draw.text((120, 1070), reel.social_growth_pack.hook_title[:42], fill="#FFFFFF", font=get_font(26, False))

        draw.text((120, 1380), "FOLLOW FOR DAILY 9:16 CODE SHOTS", fill=reel.brand_kit.primary_color, font=get_font(24, True))
