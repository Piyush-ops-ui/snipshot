"""
Reel Generator:
Real 9:16 .mp4 Video Rendering Engine (OpenCV + Pillow + Pygments + FFmpeg).
Generates production-grade 1080x1920 MP4 reels with:
- Top Section (1080x160): Institute Brand Kit Header (Brand Color, Name, Logo).
- Upper-Middle Section (1080x640): Clean, syntax-highlighted Code/Key-Notes Spotlight Card (Pygments + Pillow, 28px monospace font).
- Lower-Middle Section (1080x760): Active Screen Region Follow with dead-zone camera and Gaussian secret blur.
- Bottom Section (1080x360): Synchronized Word-by-Word Karaoke Subtitles burned into frames.
Stitches frames with sliced audio using Intel Arc QSV or ultrafast libx264 for instant native browser playback.
"""

from typing import Optional, List, Tuple, Dict, Any
from pathlib import Path
import os
import subprocess
import gc
import re
import numpy as np

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
    import pygments
    from pygments.lexers import get_lexer_by_name, guess_lexer, PythonLexer, JavascriptLexer
    from pygments.token import Token
    PYGMENTS_AVAILABLE = True
except ImportError:
    pygments = None
    PYGMENTS_AVAILABLE = False

from backend.app.schemas.reel_ir import WordAlignment, RedactionBox
from backend.app.schemas.brand import BrandKitConfig as BrandKit
from backend.app.core.mode_a_pipeline import HighlightClip
from backend.app.services.ffmpeg_service import FFmpegService
from backend.app.config import settings


# VS Code Dark+ / Modern Syntax Theme Palette
PYGMENTS_TOKEN_COLORS = {
    Token.Keyword: "#F43F5E",                # Rose / Magenta
    Token.Keyword.Constant: "#C084FC",       # Purple
    Token.Keyword.Declaration: "#F43F5E",
    Token.Keyword.Namespace: "#F43F5E",
    Token.Keyword.Type: "#38BDF8",           # Sky Cyan
    Token.Name: "#F8FAFC",                   # White
    Token.Name.Function: "#38BDF8",          # Cyan
    Token.Name.Class: "#38BDF8",
    Token.Name.Decorator: "#FBBF24",         # Amber
    Token.Name.Builtin: "#38BDF8",
    Token.Literal.String: "#34D399",         # Emerald Green
    Token.Literal.Number: "#FBBF24",         # Amber
    Token.Operator: "#E2E8F0",
    Token.Punctuation: "#94A3B8",            # Gray
    Token.Comment: "#64748B",                # Slate Muted
    Token.Comment.Single: "#64748B",
    Token.Comment.Multiline: "#64748B",
    Token.Generic: "#F8FAFC",
}


def get_system_font(size: int = 24, monospace: bool = True) -> ImageFont.ImageFont:
    """Loads bundled or system TrueType font with graceful fallback."""
    if not PILLOW_AVAILABLE:
        return None
    candidates = [
        str(settings.FONTS_DIR / "JetBrainsMono-Bold.ttf"),
        str(settings.FONTS_DIR / "Inter-SemiBold.ttf"),
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]
    for c in candidates:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                pass
    return ImageFont.load_default()


class ReelGenerator:
    WIDTH: int = 1080
    HEIGHT: int = 1920

    # Vertical Section Partitions (Total = 1920)
    SECTION_TOP_H: int = 160       # y: 0 to 160
    SECTION_CODE_H: int = 640      # y: 160 to 800
    SECTION_SCREEN_H: int = 760    # y: 800 to 1560
    SECTION_SUB_H: int = 360       # y: 1560 to 1920

    def __init__(
        self,
        ffmpeg_service: Optional[FFmpegService] = None,
        outputs_dir: Optional[Path] = None,
        cache_dir: Optional[Path] = None,
    ):
        self.ffmpeg = ffmpeg_service or FFmpegService()
        self.outputs_dir = outputs_dir or (settings.BASE_DIR / "backend" / "outputs")
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir = cache_dir or settings.CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def slice_audio_for_clip(
        self,
        source_audio_path: str,
        start_sec: float,
        duration: float,
        clip_id: str,
    ) -> str:
        """Slices precise audio segment for the highlight clip."""
        sliced_wav = str(self.cache_dir / f"slice_{clip_id}.wav")
        cmd = [
            self.ffmpeg.ffmpeg_bin,
            "-y",
            "-ss", str(start_sec),
            "-i", source_audio_path,
            "-t", str(duration),
            "-c:a", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            sliced_wav,
        ]
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True)
        except Exception:
            # Fallback to full audio if slice command fails
            return source_audio_path
        return sliced_wav

    def render_reel(
        self,
        clip_id: str,
        source_video_path: str,
        audio_path: str,
        start_sec: float,
        end_sec: float,
        words: List[WordAlignment],
        code_snippet: Optional[str] = None,
        redaction_boxes: Optional[List[RedactionBox]] = None,
        brand_kit: Optional[BrandKit] = None,
        fps: int = 30,
    ) -> str:
        """
        Renders complete real 1080x1920 .mp4 video saved in backend/outputs/reel_<id>.mp4:
        1. Top Section (1080x160): Brand kit header.
        2. Upper-Middle Section (1080x640): Syntax-highlighted code card.
        3. Lower-Middle Section (1080x760): Active screen region follow with secret blur.
        4. Bottom Section (1080x360): Synchronized word-by-word karaoke subtitles.
        """
        if not PILLOW_AVAILABLE:
            raise RuntimeError("Pillow is required for video composition.")

        gc.collect()

        duration = max(1.0, end_sec - start_sec)
        total_frames = int(duration * fps)
        output_mp4_path = str(self.outputs_dir / f"reel_{clip_id}.mp4")

        # Slice matching audio segment
        sliced_audio = self.slice_audio_for_clip(audio_path, start_sec, duration, clip_id)

        # Brand kit defaults
        if brand_kit is None:
            brand_kit = BrandKit(
                name="TechSummitTrainers",
                primary_color="#00F2FE",
                secondary_color="#38BDF8",
                background_color="#0B0F19",
                watermark_text="TechSummitTrainers",
            )

        # Pre-cache fonts
        header_title_font = get_system_font(30, monospace=False)
        header_badge_font = get_system_font(18, monospace=True)
        code_font = get_system_font(26, monospace=True)
        sub_main_font = get_system_font(34, monospace=False)
        sub_active_font = get_system_font(38, monospace=False)
        badge_font = get_system_font(20, monospace=True)

        # Open source video capture
        cap = None
        source_w, source_h = 1920, 1080
        if CV2_AVAILABLE and os.path.exists(source_video_path):
            cap = cv2.VideoCapture(source_video_path)
            source_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 1920)
            source_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 1080)

        # Prepare Pygments syntax highlighted tokens
        tokenized_code_lines = self._tokenize_code_snippet(code_snippet)

        # Seek once to start_sec
        if cap is not None and cap.isOpened():
            cap.set(cv2.CAP_PROP_POS_MSEC, start_sec * 1000.0)

        # Open FFmpeg subprocess pipe
        proc = self._open_ffmpeg_writer(output_mp4_path, sliced_audio, fps)

        redactions = redaction_boxes or []

        # Online camera dead-zone tracking state
        crop_w = min(source_w, int(source_h * (float(self.WIDTH) / self.SECTION_SCREEN_H)))
        min_x = crop_w / 2.0
        max_x = source_w - (crop_w / 2.0)
        cur_cam_x = float(source_w / 2)
        dead_zone_radius = crop_w * 0.15
        alpha = 0.20
        prev_small_gray = None
        last_valid_frame = None

        try:
            for frame_idx in range(total_frames):
                rel_time = frame_idx / fps
                abs_time = start_sec + rel_time

                # Sequential frame read (10x faster than random seeking)
                frame_bgr = None
                if cap is not None and cap.isOpened():
                    ret, f_read = cap.read()
                    if ret and f_read is not None:
                        frame_bgr = f_read
                        last_valid_frame = f_read
                    elif last_valid_frame is not None:
                        frame_bgr = last_valid_frame.copy()

                # On-the-fly camera tracking
                if frame_bgr is not None and frame_idx % 2 == 0:
                    small = cv2.resize(frame_bgr, (160, 90), interpolation=cv2.INTER_NEAREST)
                    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
                    if prev_small_gray is not None:
                        diff = cv2.absdiff(gray, prev_small_gray)
                        w_third = 160 // 3
                        act_left = float(np.mean(diff[:, :w_third]))
                        act_center = float(np.mean(diff[:, w_third : 2 * w_third]))
                        act_right = float(np.mean(diff[:, 2 * w_third :]))

                        if act_left > act_center and act_left > act_right and act_left > 1.5:
                            target_x = min_x
                        elif act_right > act_center and act_right > act_left and act_right > 1.5:
                            target_x = max_x
                        else:
                            target_x = float(source_w / 2)

                        dist = target_x - cur_cam_x
                        if abs(dist) > dead_zone_radius:
                            cur_cam_x += alpha * dist
                        cur_cam_x = max(min_x, min(max_x, cur_cam_x))
                    prev_small_gray = gray

                # 1. Base Canvas
                img = Image.new("RGBA", (self.WIDTH, self.HEIGHT), color=brand_kit.background_color)
                draw = ImageDraw.Draw(img)

                # 2. Section 1: Institute Brand Kit Header (1080x160)
                self._draw_brand_header(draw, brand_kit, rel_time, duration, header_title_font, header_badge_font)

                # 3. Section 2: Code Spotlight Card (1080x640)
                self._draw_code_spotlight_card(draw, tokenized_code_lines, brand_kit, code_font)

                # 4. Section 3: Active Screen Region Follow (1080x760)
                self._draw_screen_video_layer(frame_bgr, img, abs_time, cur_cam_x, source_w, source_h, redactions)

                # 5. Section 4: Synchronized Word-by-Word Karaoke Subtitles (1080x360)
                self._draw_karaoke_subtitles(
                    draw, words, rel_time, brand_kit, sub_main_font, sub_active_font, badge_font
                )

                # 6. Bottom Progress Bar
                self._draw_progress_bar(draw, rel_time, duration, brand_kit.primary_color)

                # Write RGBA frame directly into FFmpeg stdin
                proc.stdin.write(img.tobytes())

            proc.stdin.close()
            proc.wait()

        finally:
            if cap is not None:
                cap.release()

        return output_mp4_path

    def _open_ffmpeg_writer(self, output_path: str, audio_path: str, fps: int) -> subprocess.Popen:
        """Spawns FFmpeg subprocess to encode RGBA stream into native browser MP4."""
        gc.collect()
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        cmd = [
            self.ffmpeg.ffmpeg_bin,
            "-y",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-s", f"{self.WIDTH}x{self.HEIGHT}",
            "-pix_fmt", "rgba",
            "-r", str(fps),
            "-i", "-",  # Read from stdin
        ]

        if audio_path and os.path.exists(audio_path):
            cmd.extend(["-i", audio_path])

        # Hardware acceleration check: Intel Arc QSV vs ultrafast libx264
        if self.ffmpeg.probe_qsv_support():
            cmd.extend(["-c:v", "h264_qsv", "-global_quality", "21"])
        else:
            cmd.extend(["-c:v", "libx264", "-preset", "ultrafast", "-crf", "21", "-threads", "8"])

        cmd.extend(["-pix_fmt", "yuv420p"])

        if audio_path and os.path.exists(audio_path):
            cmd.extend(["-c:a", "aac", "-b:a", "192k", "-shortest"])

        # Add FastStart flag for instant web streaming
        cmd.extend(["-movflags", "+faststart", output_path])

        return subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )

    def _tokenize_code_snippet(self, code_snippet: Optional[str]) -> List[List[Tuple[str, str]]]:
        """Tokenizes code snippet with Pygments for high-contrast syntax highlighting."""
        snippet = code_snippet or "# Highlight Code Snippet\nprint('SnipShot Spotlight')"
        lines = snippet.strip().split("\n")[:11]

        tokenized_lines = []
        if PYGMENTS_AVAILABLE:
            try:
                lexer = guess_lexer(snippet)
            except Exception:
                lexer = JavascriptLexer()

            for line in lines:
                tokens = []
                for tok_type, tok_val in pygments.lex(line, lexer):
                    color = "#F8FAFC"
                    for pattern, col in PYGMENTS_TOKEN_COLORS.items():
                        if tok_type in pattern:
                            color = col
                            break
                    tokens.append((tok_val, color))
                tokenized_lines.append(tokens)
        else:
            for line in lines:
                tokenized_lines.append([(line, "#38BDF8")])

        return tokenized_lines

    def _compute_active_camera_trajectory(
        self,
        cap,
        start_sec: float,
        duration: float,
        fps: int,
        source_w: int,
        source_h: int,
    ) -> List[float]:
        """
        Measures pixel changes (cv2.absdiff) across left/center/right regions
        and applies a smooth dead-zone camera filter so the crop follows active typing/diagrams.
        """
        total_frames = int(duration * fps)
        default_x = float(source_w / 2)
        if cap is None or not CV2_AVAILABLE:
            return [default_x] * total_frames

        # Crop width for 1080x760 section:
        # Aspect 1080 / 760 = 1.421 => crop width at height source_h is min(source_w, int(source_h * 1.421))
        crop_w = min(source_w, int(source_h * (1080.0 / 760.0)))
        min_x = crop_w / 2.0
        max_x = source_w - (crop_w / 2.0)

        # Sample at 2 FPS to calculate regional activity without slowing down
        sample_step = max(1, fps // 2)
        cur_x = default_x
        trajectory: List[float] = []

        prev_gray = None
        cap.set(cv2.CAP_PROP_POS_MSEC, start_sec * 1000.0)

        dead_zone_radius = crop_w * 0.15  # 15% inner dead-zone
        alpha = 0.20                      # Smoothing factor

        sampled_positions = []
        for f in range(0, total_frames, sample_step):
            ret, frame = cap.read()
            if not ret or frame is None:
                sampled_positions.append(cur_x)
                continue

            small = cv2.resize(frame, (320, 180), interpolation=cv2.INTER_NEAREST)
            gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)

            if prev_gray is not None:
                diff = cv2.absdiff(gray, prev_gray)
                w_third = 320 // 3
                act_left = float(np.mean(diff[:, :w_third]))
                act_center = float(np.mean(diff[:, w_third : 2 * w_third]))
                act_right = float(np.mean(diff[:, 2 * w_third :]))

                # Determine target center based on active region
                if act_left > act_center and act_left > act_right and act_left > 2.0:
                    target_x = min_x
                elif act_right > act_center and act_right > act_left and act_right > 2.0:
                    target_x = max_x
                else:
                    target_x = default_x

                dist = target_x - cur_x
                if abs(dist) > dead_zone_radius:
                    cur_x += alpha * dist

                cur_x = max(min_x, min(max_x, cur_x))

            prev_gray = gray
            sampled_positions.append(cur_x)

        # Interpolate sampled positions to full frame rate
        for f in range(total_frames):
            s_idx = min(f // sample_step, len(sampled_positions) - 1)
            trajectory.append(sampled_positions[s_idx])

        return trajectory

    def _draw_brand_header(self, draw, brand_kit: BrandKit, rel_time: float, total_duration: float, title_font, badge_font):
        """Top Section (1080x160): Institute Brand Kit Header."""
        header_y0, header_y1 = 0, self.SECTION_TOP_H
        draw.rectangle([(0, header_y0), (self.WIDTH, header_y1)], fill="#080C14")
        # Bottom accent divider line
        draw.line([(0, header_y1 - 2), (self.WIDTH, header_y1 - 2)], fill=brand_kit.primary_color, width=2)

        # Brand Icon / Logo Capsule
        draw.rounded_rectangle([(40, 42), (110, 118)], radius=14, fill="#0F172A", outline=brand_kit.primary_color, width=2)
        draw.text((54, 60), ">_", fill=brand_kit.primary_color, font=title_font)

        # Institute Name
        name_text = (brand_kit.name or brand_kit.watermark_text or "TechSummitTrainers").upper()
        draw.text((130, 48), name_text, fill="#FFFFFF", font=title_font)

        # Mode Badge
        draw.text((132, 92), "SNIPSHOT 9:16 • PEDAGOGICAL CODE SHOT", fill="#94A3B8", font=badge_font)

        # Top-Right Verified Badge
        draw.rounded_rectangle([(self.WIDTH - 280, 52), (self.WIDTH - 40, 108)], radius=12, fill="#0F172A", outline="#38BDF8", width=2)
        draw.text((self.WIDTH - 262, 68), "SCREEN-GROUNDED", fill="#38BDF8", font=badge_font)

    def _draw_code_spotlight_card(self, draw, tokenized_lines: List[List[Tuple[str, str]]], brand_kit: BrandKit, code_font):
        """Upper-Middle Section (1080x640): Clean formatted Code/Key-Notes Spotlight Card."""
        card_x0, card_x1 = 30, self.WIDTH - 30
        card_y0, card_y1 = 180, 780

        # Card container
        draw.rounded_rectangle([(card_x0, card_y0), (card_x1, card_y1)], radius=20, fill="#0A0E1A", outline="#1E293B", width=2)

        # Window Header Tab
        tab_y1 = card_y0 + 52
        draw.rounded_rectangle([(card_x0, card_y0), (card_x1, tab_y1)], radius=18, fill="#131B2E")
        # Window Controls (macOS style)
        draw.ellipse([(card_x0 + 24, card_y0 + 18), (card_x0 + 40, card_y0 + 34)], fill="#EF4444")
        draw.ellipse([(card_x0 + 48, card_y0 + 18), (card_x0 + 64, card_y0 + 34)], fill="#F59E0B")
        draw.ellipse([(card_x0 + 72, card_y0 + 18), (card_x0 + 88, card_y0 + 34)], fill="#10B981")

        # Tab Title & Badge
        draw.text((card_x0 + 110, card_y0 + 15), "KEY CODE SPOTLIGHT", fill="#94A3B8", font=get_system_font(18, True))
        draw.rounded_rectangle([(card_x1 - 180, card_y0 + 10), (card_x1 - 20, card_y0 + 42)], radius=10, fill="#0F172A", outline=brand_kit.primary_color, width=1)
        draw.text((card_x1 - 165, card_y0 + 16), "100% READABLE", fill=brand_kit.primary_color, font=get_system_font(16, True))

        # Render code lines with syntax colors
        line_y = tab_y1 + 22
        for line_num, tokens in enumerate(tokenized_lines):
            # Line number
            draw.text((card_x0 + 24, line_y), f"{line_num + 1:2d} ", fill="#475569", font=code_font)

            cur_x = card_x0 + 80
            for text, color in tokens:
                draw.text((cur_x, line_y), text, fill=color, font=code_font)
                try:
                    tok_w = int(draw.textlength(text, font=code_font))
                except Exception:
                    tok_w = len(text) * 16
                cur_x += tok_w

            line_y += 42
            if line_y > card_y1 - 30:
                break

    def _draw_screen_video_layer(
        self, frame_bgr: Optional[np.ndarray], img: Image.Image, abs_time: float, cam_x: float,
        source_w: int, source_h: int, redaction_boxes: List[RedactionBox]
    ):
        """
        Lower-Middle Section (1080x760):
        Applies Gaussian blur on secrets, crops active region according to smooth dead-zone camera,
        and pastes into canvas.
        """
        target_h = self.SECTION_SCREEN_H  # 760
        target_w = self.WIDTH             # 1080
        y_offset = 800

        if frame_bgr is None or not CV2_AVAILABLE:
            # Fallback synthetic terminal canvas
            synth = Image.new("RGBA", (target_w, target_h), color="#0F172A")
            d = ImageDraw.Draw(synth)
            d.text((40, 40), "> SCREEN CAPTURE VIEWPORT", fill="#38BDF8", font=get_system_font(24, True))
            img.paste(synth, (0, y_offset))
            return

        frame_bgr = frame_bgr.copy()

        # Weapon 5: SafeCohort Secret & PII Blur Shield
        for rbox in redaction_boxes:
            if rbox.start <= abs_time <= rbox.end:
                rx, ry, rw, rh = [int(v) for v in rbox.box]
                rx = max(0, min(source_w - 1, rx))
                ry = max(0, min(source_h - 1, ry))
                rw = max(1, min(source_w - rx, rw))
                rh = max(1, min(source_h - ry, rh))
                pad = 20
                y0 = max(0, ry - pad)
                y1 = min(source_h, ry + rh + pad)
                x0 = max(0, rx - pad)
                x1 = min(source_w, rx + rw + pad)
                roi = frame_bgr[y0:y1, x0:x1]
                if roi.size > 0:
                    blurred = cv2.GaussianBlur(roi, (51, 51), 0)
                    frame_bgr[ry : ry + rh, rx : rx + rw] = blurred[
                        ry - y0 : ry - y0 + rh, rx - x0 : rx - x0 + rw
                    ]

        # Calculate crop coordinates using camera center cam_x
        crop_w = min(source_w, int(source_h * (float(target_w) / target_h)))
        x0 = max(0, min(source_w - crop_w, int(cam_x - (crop_w / 2.0))))
        x1 = x0 + crop_w
        crop_bgr = frame_bgr[0 : source_h, x0 : x1]

        if crop_bgr.size > 0:
            resized_bgr = cv2.resize(crop_bgr, (target_w, target_h), interpolation=cv2.INTER_LINEAR)
            resized_rgb = cv2.cvtColor(resized_bgr, cv2.COLOR_BGR2RGB)
            pil_screen = Image.fromarray(resized_rgb)
            img.paste(pil_screen, (0, y_offset))

    def _draw_karaoke_subtitles(
        self, draw, words: List[WordAlignment], rel_time: float,
        brand_kit: BrandKit, main_font, active_font, badge_font
    ):
        """Bottom Section (1080x360): Synchronized Word-by-Word Karaoke Subtitles."""
        sub_y0, sub_y1 = 1580, 1890
        sub_x0, sub_x1 = 30, self.WIDTH - 30

        # Subtitle HUD box
        draw.rounded_rectangle([(sub_x0, sub_y0), (sub_x1, sub_y1)], radius=22, fill="#0B0F19", outline="#1E293B", width=2)

        # Find active word
        active_word = None
        for w in words:
            if w.start <= rel_time <= w.end:
                active_word = w
                break

        # Provenance badge if active word was repaired
        if active_word and (active_word.is_technical or active_word.raw_asr_word):
            badge_text = f"SCREEN PROVENANCE: {active_word.word}"
            draw.rounded_rectangle([(sub_x0 + 30, sub_y0 - 24), (sub_x0 + 440, sub_y0 + 12)], radius=10, fill="#0284C7")
            draw.text((sub_x0 + 45, sub_y0 - 20), badge_text, fill="#FFFFFF", font=badge_font)

        # Context window: current 5 to 7 words
        window_words = [w for w in words if (rel_time - 1.8) <= w.start <= (rel_time + 1.8)]
        if not window_words and words:
            closest = min(words, key=lambda w: abs(w.start - rel_time))
            window_words = [closest]

        # Draw subtitle line
        cur_x = sub_x0 + 40
        line_y = sub_y0 + 45

        for w in window_words:
            is_active = (active_word is not None and w.id == active_word.id)
            word_str = w.word + " "

            if is_active:
                f = active_font
                color = brand_kit.primary_color
                try:
                    w_len = int(draw.textlength(word_str, font=f))
                except Exception:
                    w_len = len(word_str) * 22

                # Highlight capsule behind active word
                draw.rounded_rectangle(
                    [(cur_x - 6, line_y - 4), (cur_x + w_len + 6, line_y + 44)],
                    radius=10,
                    fill="#1E293B",
                    outline=brand_kit.primary_color,
                    width=2,
                )
                draw.text((cur_x, line_y), word_str, fill=color, font=f)
                cur_x += w_len + 14
            else:
                f = main_font
                color = "#94A3B8"
                draw.text((cur_x, line_y + 4), word_str, fill=color, font=f)
                try:
                    w_len = int(draw.textlength(word_str, font=f))
                except Exception:
                    w_len = len(word_str) * 20
                cur_x += w_len + 8

            if cur_x > sub_x1 - 60:
                break

    def _draw_progress_bar(self, draw, rel_time: float, total_duration: float, color: str):
        """Smooth animated progress bar at the very bottom edge."""
        bar_y0, bar_y1 = self.HEIGHT - 12, self.HEIGHT
        ratio = min(1.0, max(0.0, rel_time / total_duration))
        progress_w = int(self.WIDTH * ratio)

        draw.rectangle([(0, bar_y0), (self.WIDTH, bar_y1)], fill="#1E293B")
        draw.rectangle([(0, bar_y0), (progress_w, bar_y1)], fill=color)
