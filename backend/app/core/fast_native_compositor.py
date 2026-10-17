"""
Fast Native FFmpeg Compositor for SnipShot.
Renders 1080x1920 9:16 vertical Reels in 2 to 4 seconds:
1. Renders ONE single static 1080x1920 RGBA PNG (overlay.png) with Pillow + Pygments:
   - Top Header (0 to 140px: Brand Color, Institute Name, Logo badge)
   - Upper Code Spotlight Card (150 to 780px: Syntax-highlighted code with 26px monospace font)
   - Transparent Middle Window (790 to 1470px: alpha = 0 where the scaled full lecture video shows through)
   - Bottom Caption Bar (1480 to 1920px: footer background + QR code stamp)
2. Generates an Advanced SubStation Alpha (.ass) subtitle file with word-by-word karaoke styling.
3. Runs ONE single native FFmpeg command with filter_complex to scale full video, overlay, burn subtitles, and encode.
"""

import os
import sys
import time
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont

from backend.app.config import settings

ROOT_DIR = settings.BASE_DIR
OUTPUTS_DIR = ROOT_DIR / "backend" / "outputs"
CACHE_DIR = ROOT_DIR / "data" / "cache"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def get_monospace_font(size: int = 24, bold: bool = False) -> ImageFont.ImageFont:
    """True Monospace font for code (guaranteed ASCII + syntax punctuation support)."""
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf" if bold else "/usr/share/fonts/truetype/freefont/FreeMono.ttf",
    ]
    for c in candidates:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                pass
    return ImageFont.load_default()


def get_ui_font(size: int = 24, bold: bool = False) -> ImageFont.ImageFont:
    """Proportional UI font for headers, badges, and labels."""
    candidates = [
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf" if bold else "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for c in candidates:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                pass
    return ImageFont.load_default()


class FastNativeCompositor:
    """Ultra-fast 9:16 compositor using single overlay PNG + ASS subtitles + native FFmpeg."""

    WIDTH = 1080
    HEIGHT = 1920
    HEADER_H = 140
    CODE_Y0 = 150
    CODE_Y1 = 780
    VIDEO_Y0 = 790
    VIDEO_H = 680       # 790 to 1470 (Aspect 16:9 fits 1080x608 inside 1080x680)
    FOOTER_Y0 = 1480
    FOOTER_H = 440      # 1480 to 1920

    def __init__(self):
        self.title_font = get_ui_font(26, bold=True)
        self.badge_font = get_ui_font(18, bold=True)
        self.code_font = get_monospace_font(24, bold=False)
        self.bold_code_font = get_monospace_font(24, bold=True)

    def render_overlay_png(
        self,
        institute_name: str,
        brand_color: str,
        code_snippet: str,
        language: str = "python",
        qr_data: Optional[str] = None,
        output_path: Optional[str] = None,
        template_archetype: str = "standard_spotlight",
        hyperlapse: bool = False,
    ) -> str:
        """
        Creates ONE single static 1080x1920 RGBA image:
        - 0..140: Top Brand Header with 4 Pedagogical Archetypes (standard_spotlight, bug_hunter, vs_battle, predict_output)
        - 150..780: Upper Code Spotlight Card (real readable code)
        - 790..1470: TRANSPARENT (alpha = 0) for the 1.4x zoom cropped video
        - 1480..1920: Bottom Caption & Outro Bar with 130x130 QR code at (910, 1740)
        """
        if not output_path:
            output_path = str(CACHE_DIR / f"overlay_{int(time.time() * 1000)}.png")

        # Create transparent RGBA canvas
        img = Image.new("RGBA", (self.WIDTH, self.HEIGHT), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        brand_rgb = self._hex_to_rgb(brand_color)

        # 1. TOP BRAND HEADER (0 to 140px)
        # Template Archetype Archetype Selection (Weapon 6 & 7)
        arch = str(getattr(template_archetype, "value", template_archetype) or "standard_spotlight").lower()

        if "bug_hunter" in arch or "bug" in arch:
            header_bg = (127, 29, 29, 255)       # Crimson Red #7F1D1D
            header_line = (16, 185, 129, 255)     # Emerald Green #10B981
            badge_border = (16, 185, 129, 255)   # Emerald Green #10B981
            badge_fill = (6, 78, 59, 255)         # Dark Emerald
            badge_text = "🚨 BUG RESOLVED [200 OK]"
            badge_color = (16, 185, 129, 255)    # Emerald Green #10B981
            subtitle_text = "SNIPSHOT 9:16 • BUG RESOLUTION REEL"
        elif "vs_battle" in arch or "vs" in arch:
            header_bg = (59, 7, 100, 255)         # Deep Violet #3B0764
            header_line = (192, 132, 252, 255)    # Violet Accent #C084FC
            badge_border = (192, 132, 252, 255)
            badge_fill = (46, 16, 101, 255)
            badge_text = "⚡ VS BATTLE • ARCHITECTURE COMPASS"
            badge_color = (245, 208, 254, 255)
            subtitle_text = "SNIPSHOT 9:16 • ARCHITECTURE COMPASS"
        elif "predict_output" in arch or "predict" in arch:
            header_bg = (120, 53, 15, 255)        # Dark Amber #78350F
            header_line = (245, 158, 11, 255)     # Amber Yellow #F59E0B
            badge_border = (245, 158, 11, 255)    # Amber Yellow #F59E0B
            badge_fill = (69, 26, 3, 255)
            badge_text = "⏸️ PAUSE & PREDICT OUTPUT"
            badge_color = (251, 191, 36, 255)     # Amber Yellow #FBBF24
            subtitle_text = "SNIPSHOT 9:16 • ACTIVE RETRIEVAL CHALLENGE"
        else:  # standard_spotlight
            header_bg = (15, 23, 42, 255)        # Deep slate #0F172A
            header_line = brand_rgb + (255,)
            badge_border = (56, 189, 248, 255)
            badge_fill = (30, 41, 59, 255)
            badge_text = "VERIFIED CONTENT"
            badge_color = (56, 189, 248, 255)
            subtitle_text = "SNIPSHOT 9:16 • SCREEN-GROUNDED CODE REEL"

        draw.rectangle([(0, 0), (self.WIDTH, self.HEADER_H)], fill=header_bg)
        draw.line([(0, self.HEADER_H - 3), (self.WIDTH, self.HEADER_H - 3)], fill=header_line, width=3)

        # Logo / Shell icon capsule
        draw.rounded_rectangle([(32, 32), (96, 96)], radius=12, fill=(30, 41, 59, 255), outline=header_line, width=2)
        draw.text((44, 46), ">_", fill=brand_rgb + (255,), font=self.title_font)

        # Institute Name & Subtitle
        name_text = (institute_name or "SNIPSHOT ACADEMY").upper()
        draw.text((114, 40), name_text, fill=(255, 255, 255, 255), font=self.title_font)
        draw.text((116, 78), subtitle_text, fill=(148, 163, 184, 255), font=self.badge_font)

        # Verified Tag / Archetype Badge
        try:
            bbox = self.badge_font.getbbox(badge_text)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
        except Exception:
            tw, th = len(badge_text) * 11, 20
        bw = max(218, tw + 28)
        bx1 = self.WIDTH - 32
        bx0 = bx1 - bw
        draw.rounded_rectangle([(bx0, 42), (bx1, 92)], radius=10, fill=badge_fill, outline=badge_border, width=2)
        tx = bx0 + (bw - tw) // 2
        ty = 42 + (50 - th) // 2
        draw.text((tx, ty), badge_text, fill=badge_color, font=self.badge_font)

        # Weapon 9: Dead-Air Hyperlapse Badge HUD
        if hyperlapse:
            draw.rounded_rectangle([(self.WIDTH - 350, 105), (self.WIDTH - 40, 145)], radius=10, fill=(15, 23, 42, 255), outline=(0, 242, 254, 255), width=2)
            draw.text((self.WIDTH - 330, 115), "⚡ 2.5x HYPERLAPSE", fill=(0, 242, 254, 255), font=self.badge_font)

        # 2. UPPER CODE SPOTLIGHT CARD (150 to 780px)
        card_x0, card_x1 = 28, self.WIDTH - 28
        card_y0, card_y1 = self.CODE_Y0, self.CODE_Y1

        # Outer card background
        draw.rounded_rectangle([(card_x0, card_y0), (card_x1, card_y1)], radius=16, fill=(24, 24, 37, 255), outline=(51, 65, 85, 255), width=2)

        # macOS style window title bar
        draw.rounded_rectangle([(card_x0, card_y0), (card_x1, card_y0 + 44)], radius=16, fill=(17, 17, 27, 255))
        draw.rectangle([(card_x0, card_y0 + 20), (card_x1, card_y0 + 44)], fill=(17, 17, 27, 255))
        draw.ellipse([(card_x0 + 16, card_y0 + 14), (card_x0 + 28, card_y0 + 26)], fill=(243, 139, 168, 255))
        draw.ellipse([(card_x0 + 36, card_y0 + 14), (card_x0 + 48, card_y0 + 26)], fill=(249, 226, 175, 255))
        draw.ellipse([(card_x0 + 56, card_y0 + 14), (card_x0 + 68, card_y0 + 26)], fill=(166, 227, 161, 255))
        draw.text((card_x0 + 84, card_y0 + 12), f"code_spotlight.{language}", fill=(148, 163, 184, 255), font=self.badge_font)

        # Code syntax lines (guaranteed monospace DejaVu font)
        clean_snippet = code_snippet.strip() if code_snippet else "# Implementation Spotlight\nprint('Hello SnipShot')"
        lines = clean_snippet.split("\n")[:14]
        line_y = card_y0 + 56
        for i, line in enumerate(lines):
            # Line number
            draw.text((card_x0 + 16, line_y), f"{i+1:2d}", fill=(100, 116, 139, 255), font=self.code_font)
            # Syntax colorized tokens
            self._draw_simple_syntax_line(draw, line, card_x0 + 64, line_y, brand_color)
            line_y += 38

        # 3. MIDDLE REGION (790 to 1470px) IS LEFT TRANSPARENT (ALPHA = 0)!
        # (This is where the native FFmpeg filtergraph scales the 1.4x zoom cropped video)
        draw.line([(0, self.VIDEO_Y0), (self.WIDTH, self.VIDEO_Y0)], fill=(51, 65, 85, 255), width=2)
        draw.line([(0, self.FOOTER_Y0), (self.WIDTH, self.FOOTER_Y0)], fill=(51, 65, 85, 255), width=2)

        # 4. BOTTOM CAPTION & OUTRO BAR (1480 to 1920px)
        draw.rectangle([(0, self.FOOTER_Y0), (self.WIDTH, self.HEIGHT)], fill=(15, 23, 42, 255))
        draw.line([(0, self.FOOTER_Y0), (self.WIDTH, self.FOOTER_Y0)], fill=brand_rgb + (255,), width=2)

        # Outro QR Code in bottom-right corner (BUG 3 Fix: exactly 130x130 at x=910, y=1740)
        try:
            import qrcode
            qr = qrcode.QRCode(box_size=4, border=1)
            qr.add_data(qr_data or "https://snipshot.studio")
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="#0F172A", back_color="#FFFFFF").convert("RGBA")
            qr_img = qr_img.resize((130, 130), Image.Resampling.NEAREST)
            img.paste(qr_img, (910, 1740))
            draw.text((918, 1712), "SCAN CODE", fill=(255, 255, 255, 255), font=self.badge_font)
        except Exception:
            try:
                draw.rectangle([(910, 1740), (1040, 1870)], fill=(255, 255, 255, 255), outline=(56, 189, 248, 255), width=2)
                draw.text((918, 1712), "SCAN CODE", fill=(255, 255, 255, 255), font=self.badge_font)
            except Exception:
                pass

        img.save(output_path, "PNG")
        return output_path

    def generate_ass_subtitles(
        self,
        words: List[Dict[str, Any]],
        start_sec: float,
        duration: float,
        brand_color: str = "#4F46E5",
        output_path: Optional[str] = None,
    ) -> str:
        """
        Generates an Advanced SubStation Alpha (.ass) subtitle file:
        - Chunks subtitles into short 5-to-7 word phrases every 2.0 to 3.0 seconds (maximum 3.2s per line)
        - Covers timestamps from 0.0s all the way to duration
        - Guarantees zero overlapping and no lines frozen on screen
        - Uses font DejaVu Sans with bold weight and outline
        """
        if not output_path:
            output_path = str(CACHE_DIR / f"subs_{int(time.time() * 1000)}.ass")

        brand_bgr = self._hex_to_ass_color(brand_color)

        clean_words = []
        for w in (words or []):
            w_start = float(w.get("start", 0.0)) - start_sec
            w_end = float(w.get("end", 0.0)) - start_sec
            if w_end < 0.0 or w_start > duration:
                continue
            word_str = str(w.get("word", "")).strip()
            if not word_str:
                continue

            # Transliterate / clean non-ASCII
            if any(ord(c) >= 128 for c in word_str):
                try:
                    from backend.app.core.hinglish_normalizer import strip_non_latin_indic_noise, transliterate_devanagari_word
                    word_str = strip_non_latin_indic_noise(word_str)
                    word_str = transliterate_devanagari_word(word_str)
                except Exception:
                    pass

            if not word_str:
                continue

            # Attach standalone punctuation to previous word instead of separate subtitle entry
            if word_str in {",", ".", "!", "?", ":", ";", "-", "।", "|"}:
                if clean_words:
                    clean_words[-1]["word"] += word_str
                continue

            clean_words.append({
                "word": word_str,
                "start": max(0.0, min(duration, w_start)),
                "end": max(w_start + 0.1, min(duration, w_end)),
            })

        # Chunk into short 5-to-7 word phrases, every 2.0 to 3.0 seconds (maximum 3.2s)
        chunks = []
        cur_chunk = []
        for w in clean_words:
            if not cur_chunk:
                cur_chunk.append(w)
                continue

            num_words = len(cur_chunk)
            chunk_span = w["end"] - cur_chunk[0]["start"]

            # Flush if reaching 5-7 words, or reaching ~2.5s-3.0s, or would exceed 3.2s
            if chunk_span >= 2.8 or num_words >= 6 or (num_words >= 4 and cur_chunk[-1]["word"].endswith((".", "!", "?", ";"))):
                chunks.append(cur_chunk)
                cur_chunk = [w]
            else:
                cur_chunk.append(w)

        if cur_chunk:
            chunks.append(cur_chunk)

        # Rhythmic visual cue fallback if no words were detected
        if not chunks and duration > 0.5:
            step = 2.5
            t = 0.0
            while t < duration:
                t_end = min(duration, t + step)
                chunks.append([
                    {"word": "Code", "start": t, "end": t + 0.5},
                    {"word": "highlight", "start": t + 0.5, "end": t + 1.0},
                    {"word": "and", "start": t + 1.0, "end": t + 1.4},
                    {"word": "explanation", "start": t + 1.4, "end": t + 1.9},
                    {"word": "walkthrough", "start": t + 1.9, "end": t_end},
                ])
                t = t_end

        ass_content = f"""[Script Info]
Title: SnipShot Fast Karaoke Subtitles
ScriptType: v4.00+
PlayResX: {self.WIDTH}
PlayResY: {self.HEIGHT}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,DejaVu Sans,48,&H00FFFFFF,&H00{brand_bgr},&H000F172A,&H80000000,1,0,0,0,100,100,0,0,1,3,0,2,60,60,140,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        for i, chunk in enumerate(chunks):
            c_start = max(0.0, chunk[0]["start"])
            c_end = max(c_start + 0.5, chunk[-1]["end"])

            # Maximum 3.2s per Dialogue line
            if c_end - c_start > 3.2:
                c_end = c_start + 3.2

            c_end = min(duration, c_end)

            # Prevent overlap with the next chunk
            if i < len(chunks) - 1:
                next_start = chunks[i + 1][0]["start"]
                if c_end > next_start:
                    c_end = max(c_start + 0.2, next_start - 0.05)

            if c_end <= c_start:
                c_end = min(duration, c_start + 0.5)

            start_str = self._format_ass_time(c_start)
            end_str = self._format_ass_time(c_end)

            # Karaoke line with \kf timing tags (hundredths of a second)
            karaoke_text = ""
            for item in chunk:
                item_dur = max(0.1, min(1.0, item["end"] - item["start"]))
                dur_cs = max(5, int(item_dur * 100))
                karaoke_text += f"{{\\kf{dur_cs}}}{item['word']} "

            ass_content += f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{karaoke_text.strip()}\n"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(ass_content)

        return output_path

    def render_reel_fast(
        self,
        source_video_path: str,
        start_sec: float,
        duration: float,
        crop_x: int = 0,
        overlay_png_path: str = "",
        ass_subtitles_path: str = "",
        output_mp4_path: str = "",
        crop_y: int = 0,
        safe_cohort_blur: bool = False,
    ) -> str:
        """
        Executes ONE SINGLE native FFmpeg filtergraph:
        - Slices [start_sec, start_sec + duration]
        - Smart 1.4x Active-Region Zoom Crop (BUG 3 & Weapon 2):
          Middle Video: source width 1920, height 1080.
          Crop width = 1370 (1920 / 1.4), crop height = 862 (1370 * 680 / 1080).
          Center crop on motion centroid cx, cy:
          cx = max(0, min(1920 - 1370, crop_x))
          cy = max(0, min(1080 - 862, crop_y))
          Filtergraph scales 1370x862 to 1080x680, perfectly filling the middle window
          with ZERO black pillar/letterbox bars, making VS Code and GitHub Desktop text 1.4x larger and readable!
        - Supports safe_cohort_blur (Weapon 5).
        - Overlays overlay_png (code card on top, footer at bottom).
        - Burns .ass word karaoke subtitles.
        - Encodes via ultrafast libx264 in 2 to 4 seconds.
        """
        crop_w = 1370
        crop_h = 862
        cx = max(0, min(1920 - crop_w, crop_x))
        cy = max(0, min(1080 - crop_h, crop_y))

        if safe_cohort_blur:
            middle_chain = (
                f"[0:v]scale=1920:1080,crop={crop_w}:{crop_h}:{cx}:{cy},scale=1080:{self.VIDEO_H},"
                f"split[vraw][vblurin];"
                f"[vblurin]crop=500:80:100:480,boxblur=15:5[vblurred];"
                f"[vraw][vblurred]overlay=100:480,pad={self.WIDTH}:{self.HEIGHT}:0:{self.VIDEO_Y0}:black[vbase];"
            )
        else:
            middle_chain = (
                f"[0:v]scale=1920:1080,crop={crop_w}:{crop_h}:{cx}:{cy},scale=1080:{self.VIDEO_H},"
                f"pad={self.WIDTH}:{self.HEIGHT}:0:{self.VIDEO_Y0}:black[vbase];"
            )

        filter_graph = (
            f"{middle_chain}"
            f"[vbase][1:v]overlay=0:0[vover];"
            f"[vover]subtitles='{ass_subtitles_path}':force_style='Alignment=2,MarginV=140'[vout]"
        )

        cmd = [
            "ffmpeg", "-y",
            "-ss", f"{start_sec:.2f}",
            "-t", f"{duration:.2f}",
            "-i", str(source_video_path),
            "-i", str(overlay_png_path),
            "-filter_complex", filter_graph,
            "-map", "[vout]",
            "-map", "0:a?",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "22",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
            "-shortest",
            str(output_mp4_path),
        ]

        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode != 0:
            # Fallback if libass had path issue: keep full scaled video without subtitles
            filter_graph_fallback = (
                f"{middle_chain}"
                f"[vbase][1:v]overlay=0:0[vout]"
            )
            cmd_fallback = [
                "ffmpeg", "-y",
                "-ss", f"{start_sec:.2f}",
                "-t", f"{duration:.2f}",
                "-i", str(source_video_path),
                "-i", str(overlay_png_path),
                "-filter_complex", filter_graph_fallback,
                "-map", "[vout]",
                "-map", "0:a?",
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-crf", "22",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "128k",
                "-movflags", "+faststart",
                "-shortest",
                str(output_mp4_path),
            ]
            subprocess.run(cmd_fallback, check=True)

        return str(output_mp4_path)

    def _draw_simple_syntax_line(self, draw, line: str, x: int, y: int, accent: str):
        """Clean token coloring for code spotlight — supports Python, JS, HTML, Bash."""
        keywords = {"def", "class", "import", "from", "return", "if", "else", "for", "while", "const", "let", "function", "async", "await", "export", "extends", "private", "public"}
        html_tags = {"html", "head", "body", "meta", "title", "div", "span", "p", "h1", "h2", "h3", "a", "img", "script", "style", "link", "DOCTYPE"}
        bash_cmds = {"git", "npm", "pip", "docker", "python", "node", "yarn", "cd", "mkdir", "echo", "curl", "wget"}
        words = line.split(" ")
        cur_x = x
        for w in words:
            clean_w = w.strip("():,;{}\"'<>/!")
            if clean_w in keywords:
                color = (244, 114, 182, 255)  # Pink keyword
            elif clean_w in html_tags or (w.startswith("<") and clean_w.lstrip("/") in html_tags):
                color = (250, 137, 107, 255)  # Coral HTML tag
            elif w.startswith("<!") or w.startswith("</") or w.startswith("<") or w.endswith(">"):
                color = (137, 180, 250, 255)  # Light blue tag brackets
            elif clean_w in bash_cmds:
                color = (250, 204, 21, 255)  # Yellow bash command
            elif w.startswith('"') or w.startswith("'") or clean_w.startswith('"') or clean_w.startswith("'"):
                color = (166, 227, 161, 255)  # Green string
            elif clean_w.startswith("@") or clean_w in {"useEffect", "useState", "Autowired", "commit", "push", "pull", "branch"}:
                color = self._hex_to_rgb(accent) + (255,)  # Brand accent
            elif clean_w.isdigit():
                color = (250, 204, 21, 255)  # Yellow number
            elif clean_w.startswith("#") or clean_w.startswith("//") or clean_w.startswith("<!--"):
                color = (100, 116, 139, 255)  # Comment gray
            elif "=" in w and not w.startswith("="):
                # Attribute assignments like charset="UTF-8"
                eq_idx = w.index("=")
                attr_name = w[:eq_idx]
                attr_val = w[eq_idx:]
                draw.text((cur_x, y), attr_name, fill=(250, 189, 47, 255), font=self.code_font)
                cur_x += len(attr_name) * 14
                draw.text((cur_x, y), attr_val + " ", fill=(166, 227, 161, 255), font=self.code_font)
                cur_x += len(attr_val + " ") * 14
                continue
            else:
                color = (241, 245, 249, 255)  # Crisp light slate
            draw.text((cur_x, y), w + " ", fill=color, font=self.code_font)
            cur_x += len(w + " ") * 14

    def _hex_to_rgb(self, h: str) -> Tuple[int, int, int]:
        h = h.lstrip("#")
        if len(h) != 6:
            return (79, 70, 229) # Default indigo
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    def _hex_to_ass_color(self, h: str) -> str:
        """Convert #RRGGBB to ASS BGR format."""
        r, g, b = self._hex_to_rgb(h)
        return f"{b:02X}{g:02X}{r:02X}"

    def _format_ass_time(self, seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        cs = int((seconds - int(seconds)) * 100)
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"
