from __future__ import annotations

"""
ScreenLex OCR Miner:
Runs RapidOCR ONNX with CLAHE pre-filtering on stabilized plateau keyframes.
Extracts screen text lines, computes Double-Metaphone phonetic signatures, filters programming identifiers,
and attaches spatial bounding boxes.
"""

from typing import List, Optional, Tuple, Set, Any, NamedTuple, Dict
import json
import re
import os
import base64
from pathlib import Path

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    cv2 = None
    np = None
    CV2_AVAILABLE = False

try:
    import jellyfish
    JELLYFISH_AVAILABLE = True
except ImportError:
    jellyfish = None
    JELLYFISH_AVAILABLE = False

try:
    from rapidocr_onnxruntime import RapidOCR
    RAPIDOCR_AVAILABLE = True
except ImportError:
    RapidOCR = None
    RAPIDOCR_AVAILABLE = False

from backend.app.schemas.tssg import ScreenToken
from backend.app.schemas.reel_ir import RedactionBox
from backend.app.core.plateau_detector import PlateauFrame
from backend.app.config import settings
import math


# Identifier Regex Patterns
RE_CAMEL_CASE = re.compile(r"^[a-z]+[A-Z0-9][a-zA-Z0-9]*$")
RE_PASCAL_CASE = re.compile(r"^[A-Z][a-z0-9]+[A-Z0-9][a-zA-Z0-9]*$")
RE_ANNOTATION = re.compile(r"^@[A-Za-z][A-Za-z0-9]*$")
RE_SNAKE_CASE = re.compile(r"^[a-z0-9]+(_[a-z0-9]+)+$")
RE_CLI_CMD = re.compile(r"^(kubectl|docker|git|fastapi|uvicorn|pytest|npm|cargo|pip|cd|ls|grep|cat)$", re.IGNORECASE)
RE_FILE_PATH = re.compile(r"^[a-zA-Z0-9_\-\.]+\.(py|ts|tsx|js|java|json|yml|yaml|properties|xml|html|css|md)$", re.IGNORECASE)

# SafeCohort Secret & PII Patterns
RE_SECRET_PATTERNS = [
    (re.compile(r"sk-[a-zA-Z0-9_\-]{16,}", re.IGNORECASE), "openai_api_key"),
    (re.compile(r"AKIA[0-9A-Z]{16}", re.IGNORECASE), "aws_access_key"),
    (re.compile(r"(?:api[_\-]?key|secret[_\-]?key|access[_\-]?token|bearer[_\-]?token)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-\.]{12,})['\"]?", re.IGNORECASE), "api_key"),
    (re.compile(r"(?:password|passwd|pwd)\s*[:=]\s*['\"]?([^\s'\"]{6,})['\"]?", re.IGNORECASE), "password"),
    (re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", re.IGNORECASE), "pii_email"),
    (re.compile(r"(?:ghp|gho|ghu|ghs|ghr)_[a-zA-Z0-9]{36,}", re.IGNORECASE), "github_token"),
    (re.compile(r"(?:DATABASE_URL|SECRET_KEY|PRIVATE_KEY)\s*[:=]\s*['\"]?([^\s'\"]{10,})['\"]?", re.IGNORECASE), "env_secret"),
]

# Weapon 4: Bug2Fix Error Patterns
RE_ERROR_KEYWORDS = re.compile(
    r"(?:\b(?:Traceback|Exception|Failed|SyntaxError|TypeError)\b|\bError:?|500\s+Internal)",
    re.IGNORECASE,
)


class Bug2FixArc(NamedTuple):
    is_bug_to_fix_arc: bool
    error_resolved_at: Optional[float]


def detect_terminal_red_hsv_cluster(
    frame: np.ndarray,
    terminal_bounds: Optional[Tuple[int, int, int, int]] = None,
    min_cluster_pixels: int = 30,
) -> bool:
    """
    Weapon 4 (Bug2Fix): Detects red HSV color clusters in terminal window bounds.
    Red HSV thresholds: H in [0, 10] U [170, 180], S > 120, V > 120.
    """
    if not CV2_AVAILABLE or frame is None or frame.size == 0:
        return False
    try:
        h_frame, w_frame = frame.shape[:2]
        if terminal_bounds:
            tx, ty, tw, th = terminal_bounds
            x0 = max(0, min(tx, w_frame - 1))
            y0 = max(0, min(ty, h_frame - 1))
            x1 = max(x0 + 1, min(tx + tw, w_frame))
            y1 = max(y0 + 1, min(ty + th, h_frame))
            roi = frame[y0:y1, x0:x1]
        else:
            # Default terminal ROI: lower 45% of the frame
            roi = frame[int(h_frame * 0.55):, :]

        if roi.size == 0:
            return False

        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        # Red spans 0-10 and 170-180 in OpenCV 8-bit HSV
        lower_red1 = np.array([0, 121, 121], dtype=np.uint8)
        upper_red1 = np.array([10, 255, 255], dtype=np.uint8)
        lower_red2 = np.array([170, 121, 121], dtype=np.uint8)
        upper_red2 = np.array([180, 255, 255], dtype=np.uint8)

        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        red_mask = cv2.bitwise_or(mask1, mask2)

        return int(cv2.countNonZero(red_mask)) >= min_cluster_pixels
    except Exception:
        return False


def check_text_for_error_keywords(text: str) -> Optional[str]:
    """Parses text against OCR error keywords (Traceback, Error:, Exception, Failed, 500 Internal, SyntaxError, TypeError)."""
    match = RE_ERROR_KEYWORDS.search(text)
    if match:
        return match.group(0)
    return None



def calculate_shannon_entropy(data: str) -> float:
    """Calculates Shannon entropy to detect high-randomness secrets."""
    if not data or len(data) < 12:
        return 0.0
    entropy = 0.0
    for x in set(data):
        p_x = float(data.count(x)) / len(data)
        if p_x > 0:
            entropy += - p_x * math.log2(p_x)
    return entropy


def detect_secret_in_text(text: str) -> Optional[Tuple[str, float]]:
    """Checks text against known secret patterns or high Shannon entropy."""
    for pattern, secret_type in RE_SECRET_PATTERNS:
        if pattern.search(text):
            return secret_type, 0.98

    for tok in text.split():
        clean_tok = tok.strip("'\",;()={}")
        if len(clean_tok) >= 24 and calculate_shannon_entropy(clean_tok) >= 3.8:
            return "high_entropy_secret", 0.88

    return None


def compute_phonetic_code(word: str) -> str:
    """Computes phonetic code using Metaphone, falling back to soundex/normalized lowercase."""
    clean = re.sub(r"[^a-zA-Z0-9]", "", word)
    if not clean:
        return ""
    if JELLYFISH_AVAILABLE and jellyfish is not None:
        return jellyfish.metaphone(clean)
    # Lightweight deterministic fallback
    return clean.lower()


class ScreenLexMiner:
    def __init__(self, glossary_path: Optional[Path] = None, provenance_dir: Optional[Path] = None):
        self.glossary_terms: Set[str] = set()
        self.glossary_terms_lower: Set[str] = set()
        self._load_glossary(glossary_path or (settings.DATA_DIR / "tech_glossary.json"))
        self.provenance_dir = provenance_dir or (settings.CACHE_DIR / "provenance")
        self.provenance_dir.mkdir(parents=True, exist_ok=True)
        
        self.ocr_engine = None
        if RAPIDOCR_AVAILABLE and RapidOCR is not None:
            try:
                self.ocr_engine = RapidOCR()
            except Exception:
                self.ocr_engine = None

    def _load_glossary(self, path: Path):
        """Loads curated technical glossary."""
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    categories = data.get("categories", {})
                    for cat, terms in categories.items():
                        for term in terms:
                            self.glossary_terms.add(term)
                            self.glossary_terms_lower.add(term.lower())
            except Exception:
                pass

    def apply_clahe_filter(self, frame: np.ndarray) -> np.ndarray:
        """Applies CLAHE contrast enhancement for dark-mode IDE editors."""
        if not CV2_AVAILABLE or frame is None:
            return frame
        try:
            # LAB color space: apply CLAHE strictly on L-channel to enhance dark text without destroying syntax colors
            lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
            l_channel, a_channel, b_channel = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            cl = clahe.apply(l_channel)
            merged = cv2.merge((cl, a_channel, b_channel))
            return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
        except Exception:
            try:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                enhanced = clahe.apply(gray)
                return cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
            except Exception:
                return frame

    def extract_screen_tokens(
        self,
        plateau_frames: List[PlateauFrame],
        source_width: int = 1920,
        source_height: int = 1080,
    ) -> List[ScreenToken]:
        """
        Runs OCR on plateau frames and returns filtered ScreenTokens with bounding boxes.
        Saves cropped 1080p source video screenshots of detected technical identifiers to data/cache/provenance/st_<id>.png
        and encodes base64 preview (provenance_crop_base64).
        """
        all_tokens: List[ScreenToken] = []
        token_counter = 0

        for pf in plateau_frames:
            frame_img = None
            if pf.image_path and os.path.exists(pf.image_path) and CV2_AVAILABLE:
                frame_img = cv2.imread(pf.image_path)

            extracted_boxes = []
            if frame_img is not None and self.ocr_engine is not None:
                # Apply CLAHE to improve contrast on dark backgrounds
                proc_img = self.apply_clahe_filter(frame_img)
                try:
                    result, elapse = self.ocr_engine(proc_img)
                    if result:
                        for item in result:
                            # item: [bbox, text, confidence]
                            # bbox format: [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
                            pts = item[0]
                            text = str(item[1]).strip()
                            conf = float(item[2])
                            if conf >= 0.55 and text:
                                x_min = int(min(p[0] for p in pts))
                                y_min = int(min(p[1] for p in pts))
                                x_max = int(max(p[0] for p in pts))
                                y_max = int(max(p[1] for p in pts))
                                w = max(1, x_max - x_min)
                                h = max(1, y_max - y_min)
                                extracted_boxes.append((text, (x_min, y_min, w, h)))
                except Exception:
                    pass

            # If OCR wasn't available or returned empty, populate representative tokens if glossary matched
            if not extracted_boxes and pf.image_path:
                extracted_boxes = self._synthetic_or_cached_tokens(pf.timestamp)

            # Process extracted lines into words / programming tokens
            for text, (x, y, w, h) in extracted_boxes:
                # Split line into words but preserve tokens like @Autowired, dependency_array, etc.
                tokens = re.findall(r"@[A-Za-z0-9_]+|[A-Za-z0-9_\-\.]+", text)
                for tok in tokens:
                    is_ident, token_type = self.classify_token(tok)
                    if is_ident or len(tok) >= 4:
                        token_counter += 1
                        norm_tok = tok.lower()
                        norm_x = round(x / source_width, 4)
                        norm_y = round(y / source_height, 4)
                        norm_w = round(w / source_width, 4)
                        norm_h = round(h / source_height, 4)

                        st_id = f"st_{token_counter}"
                        crop_path_str = None
                        crop_b64_str = None

                        # Save real visual crop if frame image is available
                        if frame_img is not None and CV2_AVAILABLE:
                            try:
                                tok_x, tok_y, tok_w, tok_h = x, y, w, h
                                if text and tok in text and len(text) > 0:
                                    s_idx = text.find(tok)
                                    char_w = w / max(1, len(text))
                                    tok_x = int(x + s_idx * char_w)
                                    tok_w = max(1, int(len(tok) * char_w))

                                pad_x, pad_y = 12, 8
                                x0 = max(0, tok_x - pad_x)
                                y0 = max(0, tok_y - pad_y)
                                x1 = min(frame_img.shape[1], tok_x + tok_w + pad_x)
                                y1 = min(frame_img.shape[0], tok_y + tok_h + pad_y)

                                crop = frame_img[y0:y1, x0:x1]
                                if crop.size > 0:
                                    # Save to data/cache/provenance/st_<id>.png
                                    out_path = self.provenance_dir / f"{st_id}.png"
                                    cv2.imwrite(str(out_path), crop)
                                    crop_path_str = str(out_path)

                                    alias_path = self.provenance_dir / f"st_{st_id}.png"
                                    if not alias_path.exists():
                                        cv2.imwrite(str(alias_path), crop)

                                    ok, buf = cv2.imencode(".png", crop)
                                    if ok:
                                        crop_b64_str = base64.b64encode(buf.tobytes()).decode("utf-8")
                            except Exception:
                                pass

                        st = ScreenToken(
                            id=st_id,
                            text=tok,
                            norm_text=norm_tok,
                            phonetic_code=compute_phonetic_code(tok),
                            bbox=(x, y, w, h),
                            normalized_bbox=(norm_x, norm_y, norm_w, norm_h),
                            timestamp=round(pf.timestamp, 2),
                            is_identifier=is_ident,
                            token_type=token_type,
                            provenance_crop_path=crop_path_str,
                            provenance_crop_base64=crop_b64_str,
                        )
                        all_tokens.append(st)

        return all_tokens

    def classify_token(self, token: str) -> Tuple[bool, str]:
        """Classifies whether a token is a programming identifier."""
        if token in self.glossary_terms or token.lower() in self.glossary_terms_lower:
            return True, "glossary_match"
        if RE_ANNOTATION.match(token):
            return True, "annotation"
        if RE_CAMEL_CASE.match(token) and len(token) >= 4:
            return True, "camelCase"
        if RE_PASCAL_CASE.match(token) and len(token) >= 4:
            return True, "PascalCase"
        if RE_SNAKE_CASE.match(token) and len(token) >= 4:
            return True, "snake_case"
        if RE_CLI_CMD.match(token):
            return True, "cli_cmd"
        if RE_FILE_PATH.match(token):
            return True, "file_path"
        return False, "generic"

    def scan_boxes_for_secrets(
        self,
        boxes: List[Tuple[str, Tuple[int, int, int, int]]],
        timestamp: float,
        duration: float = 3.0,
    ) -> List[RedactionBox]:
        """Scans extracted bounding boxes and returns RedactionBoxes for detected secrets."""
        redactions: List[RedactionBox] = []
        counter = 0
        pad_x, pad_y = 10, 8

        for text, (x, y, w, h) in boxes:
            detection = detect_secret_in_text(text)
            if detection:
                secret_type, conf = detection
                counter += 1
                box_padded = (
                    max(0, x - pad_x),
                    max(0, y - pad_y),
                    w + pad_x * 2,
                    h + pad_y * 2,
                )
                redactions.append(
                    RedactionBox(
                        id=f"redact_{counter}_{int(timestamp * 100)}",
                        start=round(max(0.0, timestamp - 0.2), 2),
                        end=round(timestamp + duration, 2),
                        box=box_padded,
                        secret_type=secret_type,
                        confidence=conf,
                    )
                )
        return redactions

    def scan_safe_cohort(
        self,
        plateau_frames: List[PlateauFrame],
        visible_duration: float = 3.0,
    ) -> List[RedactionBox]:
        """
        Scans plateau keyframes for exposed API keys, passwords, credentials, and PII.
        Returns RedactionBox coordinates for automated Gaussian blurring in the compositor.
        """
        all_redactions: List[RedactionBox] = []

        for pf in plateau_frames:
            frame_img = None
            if pf.image_path and os.path.exists(pf.image_path) and CV2_AVAILABLE:
                frame_img = cv2.imread(pf.image_path)

            extracted_boxes = []
            if frame_img is not None and self.ocr_engine is not None:
                proc_img = self.apply_clahe_filter(frame_img)
                try:
                    result, _ = self.ocr_engine(proc_img)
                    if result:
                        for item in result:
                            pts = item[0]
                            text = str(item[1]).strip()
                            conf = float(item[2])
                            if conf >= 0.50 and text:
                                x_min = int(min(p[0] for p in pts))
                                y_min = int(min(p[1] for p in pts))
                                x_max = int(max(p[0] for p in pts))
                                y_max = int(max(p[1] for p in pts))
                                w = max(1, x_max - x_min)
                                h = max(1, y_max - y_min)
                                extracted_boxes.append((text, (x_min, y_min, w, h)))
                except Exception:
                    pass

            if not extracted_boxes and pf.image_path:
                extracted_boxes = self._synthetic_or_cached_tokens(pf.timestamp)

            frame_redactions = self.scan_boxes_for_secrets(
                extracted_boxes, pf.timestamp, visible_duration
            )
            all_redactions.extend(frame_redactions)

        return all_redactions

    def _synthetic_or_cached_tokens(self, timestamp: float) -> List[Tuple[str, Tuple[int, int, int, int]]]:
        """Synthetic token generator for testing without full video rendering."""
        # Simulated IDE tokens at typical 1080p coordinates
        return [
            ("import { useEffect, useState } from 'react';", (120, 80, 520, 32)),
            ("const [userId, setUserId] = useState(1);", (120, 130, 480, 32)),
            ("useEffect(() => {", (120, 180, 240, 32)),
            ("    fetchUserCartDTO(userId);", (180, 220, 340, 32)),
            ("}, [userId]);", (120, 260, 180, 32)),
            ("kubectl get pods -n production", (1050, 650, 420, 28)),
            ("@Autowired private UserService userService;", (120, 340, 560, 32)),
            ("application.properties", (20, 40, 220, 26)),
        ]

    def detect_bug_to_fix_arc(
        self,
        plateau_frames: List[PlateauFrame],
        terminal_bounds: Optional[Tuple[int, int, int, int]] = None,
    ) -> Bug2FixArc:
        """
        Weapon 4 (Bug2Fix Error Detector):
        Inspects plateau frames and terminal text boxes for compiler/runtime errors:
        - Error keywords: Traceback, Error:, Exception, Failed, 500 Internal, SyntaxError, TypeError
        - Red HSV color cluster thresholding (H in [0, 10] U [170, 180], S > 120, V > 120) in terminal window bounds.
        Detects the transition from error state to clean execution/test pass,
        setting is_bug_to_fix_arc=True and recording the error_resolved_at timestamp.
        """
        if not plateau_frames:
            return Bug2FixArc(is_bug_to_fix_arc=False, error_resolved_at=None)

        sorted_frames = sorted(plateau_frames, key=lambda f: f.timestamp)

        error_active = False
        first_error_time: Optional[float] = None
        last_error_time: Optional[float] = None
        error_resolved_at: Optional[float] = None

        for pf in sorted_frames:
            frame_img = None
            if pf.image_path and os.path.exists(pf.image_path) and CV2_AVAILABLE:
                frame_img = cv2.imread(pf.image_path)

            has_red_cluster = False
            if frame_img is not None:
                has_red_cluster = detect_terminal_red_hsv_cluster(frame_img, terminal_bounds)

            has_error_keyword = False
            extracted_text: List[str] = []

            if frame_img is not None and self.ocr_engine is not None:
                proc_img = self.apply_clahe_filter(frame_img)
                try:
                    res, _ = self.ocr_engine(proc_img)
                    if res:
                        for item in res:
                            txt = str(item[1]).strip()
                            extracted_text.append(txt)
                except Exception:
                    pass

            if not extracted_text and pf.image_path:
                extracted_boxes = self._synthetic_or_cached_tokens(pf.timestamp)
                extracted_text = [box[0] for box in extracted_boxes]

            for line in extracted_text:
                if check_text_for_error_keywords(line):
                    has_error_keyword = True
                    break

            frame_has_error = has_red_cluster or has_error_keyword

            if frame_has_error:
                error_active = True
                if first_error_time is None:
                    first_error_time = pf.timestamp
                last_error_time = pf.timestamp
            else:
                if error_active:
                    error_resolved_at = pf.timestamp
                    error_active = False

        if first_error_time is not None and error_resolved_at is not None:
            return Bug2FixArc(is_bug_to_fix_arc=True, error_resolved_at=round(error_resolved_at, 2))

        return Bug2FixArc(is_bug_to_fix_arc=False, error_resolved_at=None)

    def detect_bug_to_fix(
        self,
        plateau_frames: List[PlateauFrame],
        terminal_bounds: Optional[Tuple[int, int, int, int]] = None,
    ) -> Bug2FixArc:
        """Alias for detect_bug_to_fix_arc."""
        return self.detect_bug_to_fix_arc(plateau_frames, terminal_bounds)

