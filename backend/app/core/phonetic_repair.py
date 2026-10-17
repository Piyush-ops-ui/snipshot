"""
Phonetic-Visual Repair Engine (ScreenLex-ASR Pass 2).
Uses Double Metaphone + Jaro-Winkler + Levenshtein distance against time-indexed screen OCR tokens
to repair mangled Hinglish technical terms (e.g., 'use a fact' -> 'useEffect', 'auto wired' -> '@Autowired').
Attaches source bounding-box provenance for verification in the Studio UI.
"""

from typing import List, Tuple, Optional, Dict
import re
import os
import json
from pathlib import Path

try:
    import jellyfish
    JELLYFISH_AVAILABLE = True
except ImportError:
    jellyfish = None
    JELLYFISH_AVAILABLE = False

try:
    from rapidfuzz.distance import Levenshtein, JaroWinkler
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    Levenshtein = None
    JaroWinkler = None
    RAPIDFUZZ_AVAILABLE = False

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    cv2 = None
    CV2_AVAILABLE = False

from backend.app.schemas.tssg import ScreenToken, ASRWord
from backend.app.schemas.reel_ir import WordAlignment
from backend.app.config import settings


HINDI_GRAMMATICAL_PARTICLES = {
    "mein", "ko", "se", "ka", "ki", "ke", "pe", "par", "aur", "toh", "ab", "yeh", "woh", "hai", "hain", "karein", "bina"
}


def compute_metaphone(text: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9]", "", text)
    if not clean:
        return ""
    if JELLYFISH_AVAILABLE and jellyfish is not None:
        return jellyfish.metaphone(clean)
    return clean.lower()


def string_similarity(s1: str, s2: str) -> float:
    """Calculates normalized string similarity in [0.0, 1.0]."""
    s1_norm = s1.lower().strip()
    s2_norm = s2.lower().strip()
    if s1_norm == s2_norm:
        return 1.0
    if not s1_norm or not s2_norm:
        return 0.0

    if RAPIDFUZZ_AVAILABLE and JaroWinkler is not None and Levenshtein is not None:
        jw = JaroWinkler.similarity(s1_norm, s2_norm)
        lev = Levenshtein.normalized_similarity(s1_norm, s2_norm)
        return float(0.55 * jw + 0.45 * lev)

    # Simple character set Jaccard fallback
    set1, set2 = set(s1_norm), set(s2_norm)
    jaccard = len(set1 & set2) / max(1, len(set1 | set2))
    return float(jaccard)


class PhoneticVisualRepairer:
    def __init__(
        self,
        glossary_path: Optional[Path] = None,
        patterns_path: Optional[Path] = None,
        provenance_dir: Optional[Path] = None,
    ):
        self.provenance_dir = provenance_dir or (settings.CACHE_DIR / "provenance")
        self.provenance_dir.mkdir(parents=True, exist_ok=True)
        
        self.glossary_terms: List[str] = []
        self.common_fixes: Dict[str, str] = {}
        self._load_resources(
            glossary_path or (settings.DATA_DIR / "tech_glossary.json"),
            patterns_path or (settings.DATA_DIR / "hinglish_patterns.json"),
        )

    def _load_resources(self, glossary_file: Path, patterns_file: Path):
        if glossary_file.exists():
            try:
                with open(glossary_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for cat, terms in data.get("categories", {}).items():
                        self.glossary_terms.extend(terms)
            except Exception:
                pass

        if patterns_file.exists():
            try:
                with open(patterns_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.common_fixes = data.get("common_misrecognitions", {})
            except Exception:
                pass

    def repair_transcript(
        self,
        asr_words: List[ASRWord],
        screen_tokens: List[ScreenToken],
        source_frame_provider: Optional[callable] = None,
    ) -> List[WordAlignment]:
        """
        Executes Algorithm 1: Sliding Windowed N-Gram Phonetic-Surface Repair.
        Merges 1 to 3 ASR words when they phonetically match an on-screen identifier.
        """
        repaired: List[WordAlignment] = []
        n = len(asr_words)
        i = 0
        word_id_counter = 0

        # Build temporal token index
        token_timestamps = [tok.timestamp for tok in screen_tokens]

        while i < n:
            matched = False
            best_match_k = None
            best_match_text = None
            best_match_tok = None
            best_match_sim = 0.0

            # Evaluate all sliding windows k in {1, 2, 3} to find the best match
            first_word_norm = asr_words[i].word.lower().strip()
            for k in [1, 2, 3]:
                # Hindi grammatical particles cannot start a multi-word technical term (e.g. 'mein auto wired')
                if k > 1 and first_word_norm in HINDI_GRAMMATICAL_PARTICLES:
                    continue

                if i + k <= n:
                    window = asr_words[i : i + k]
                    phrase = " ".join(w.word for w in window).strip()
                    norm_phrase = re.sub(r"[^a-zA-Z0-9]", "", phrase.lower())
                    mean_prob = sum(w.probability for w in window) / k
                    t_mid = (window[0].start + window[-1].end) / 2.0

                    # 1. Fast deterministic exact rule check
                    phrase_lower = phrase.lower()
                    if phrase_lower in self.common_fixes:
                        target = self.common_fixes[phrase_lower]
                        best_tok = self._find_matching_screen_token(target, screen_tokens, t_mid)
                        if 1.0 > best_match_sim:
                            best_match_sim = 1.0
                            best_match_k = k
                            best_match_text = target
                            best_match_tok = best_tok
                        continue

                    # 2. Search temporal candidate pool: tokens within +- 20 seconds
                    candidates: List[Tuple[str, Optional[ScreenToken], float]] = []
                    for tok in screen_tokens:
                        if abs(tok.timestamp - t_mid) <= 20.0:
                            candidates.append((tok.text, tok, 0.10))  # +0.10 co-occurrence bonus

                    # Add global glossary terms
                    for term in self.glossary_terms:
                        candidates.append((term, None, 0.0))

                    # 3. Phonetic & Surface Similarity Evaluation
                    phrase_meta = compute_metaphone(phrase)

                    for cand_text, cand_tok, bonus in candidates:
                        cand_clean = re.sub(r"[^a-zA-Z0-9]", "", cand_text.lower())
                        if not cand_clean or len(cand_clean) < 4:
                            continue

                        cand_meta = compute_metaphone(cand_text)
                        
                        # Metaphone phonetic distance
                        phonetic_match = 1.0 if (phrase_meta and phrase_meta == cand_meta) else string_similarity(phrase_meta, cand_meta)
                        surface_match = string_similarity(norm_phrase, cand_clean)
                        
                        composite_sim = (0.55 * phonetic_match) + (0.45 * surface_match) + bonus

                        threshold = 0.76 if mean_prob < 0.65 else 0.82
                        if composite_sim >= threshold and composite_sim > best_match_sim:
                            if len(cand_text) >= 5 or cand_text.startswith("@"):
                                best_match_sim = composite_sim
                                best_match_k = k
                                best_match_text = cand_text
                                best_match_tok = cand_tok

            if best_match_k is not None and best_match_text is not None:
                window = asr_words[i : i + best_match_k]
                repaired_word = self._create_alignment(
                    window=window,
                    grounded_text=best_match_text,
                    sim_score=min(1.0, best_match_sim),
                    token=best_match_tok,
                    counter=word_id_counter,
                    source_frame_provider=source_frame_provider,
                )
                repaired.append(repaired_word)
                word_id_counter += 1
                i += best_match_k
                matched = True

            if not matched:
                # Normal word, no repair needed
                w = asr_words[i]
                word_id_counter += 1
                # Check if this single word happens to be an exact technical identifier
                is_tech = w.word in self.glossary_terms or bool(re.match(r"^@[A-Za-z]+$", w.word))
                
                # Check screen token match for provenance
                matched_tok = None
                if is_tech or len(w.word) >= 4:
                    t_mid = (w.start + w.end) / 2.0
                    matched_tok = self._find_matching_screen_token(w.word, screen_tokens, t_mid)
                    if matched_tok:
                        is_tech = True

                thumb_url = None
                bbox = matched_tok.bbox if matched_tok else None
                frame_time = matched_tok.timestamp if matched_tok else None

                if matched_tok:
                    if hasattr(matched_tok, "provenance_crop_path") and matched_tok.provenance_crop_path:
                        clean_name = os.path.basename(matched_tok.provenance_crop_path)
                        thumb_url = f"/api/timeline/provenance/thumb/{clean_name}"
                    else:
                        for cand in [f"{matched_tok.id}.png", f"st_{matched_tok.id}.png"]:
                            if (self.provenance_dir / cand).exists():
                                thumb_url = f"/api/timeline/provenance/thumb/{cand}"
                                break

                repaired.append(
                    WordAlignment(
                        id=f"w_{word_id_counter}",
                        word=w.word,
                        start=round(w.start, 3),
                        end=round(w.end, 3),
                        confidence=round(w.probability, 3),
                        is_technical=is_tech,
                        provenance_frame_time=frame_time,
                        provenance_bbox=bbox,
                        provenance_thumbnail_url=thumb_url,
                    )
                )
                i += 1

        return repaired

    def _find_matching_screen_token(
        self, target: str, tokens: List[ScreenToken], t_mid: float
    ) -> Optional[ScreenToken]:
        """Finds closest temporal screen token with identical normalized text."""
        target_norm = target.lower().strip()
        best = None
        min_dist = float("inf")
        for tok in tokens:
            if tok.norm_text == target_norm:
                dist = abs(tok.timestamp - t_mid)
                if dist < min_dist:
                    min_dist = dist
                    best = tok
        return best

    def _create_alignment(
        self,
        window: List[ASRWord],
        grounded_text: str,
        sim_score: float,
        token: Optional[ScreenToken],
        counter: int,
        source_frame_provider: Optional[callable] = None,
    ) -> WordAlignment:
        raw_phrase = " ".join(w.word for w in window)
        start_t = round(window[0].start, 3)
        end_t = round(window[-1].end, 3)

        thumbnail_url = None
        bbox = token.bbox if token else None
        frame_time = token.timestamp if token else None

        # Check existing pre-generated token crop if available
        if token:
            if hasattr(token, "provenance_crop_path") and token.provenance_crop_path:
                clean_name = os.path.basename(token.provenance_crop_path)
                thumbnail_url = f"/api/timeline/provenance/thumb/{clean_name}"
            else:
                for cand in [f"{token.id}.png", f"st_{token.id}.png"]:
                    if (self.provenance_dir / cand).exists():
                        thumbnail_url = f"/api/timeline/provenance/thumb/{cand}"
                        break

        # Extract cropped thumbnail proof if frame provider and bbox exist
        if token and source_frame_provider and CV2_AVAILABLE:
            try:
                frame = source_frame_provider(token.timestamp)
                if frame is not None:
                    x, y, w, h = token.bbox
                    # Pad bbox slightly
                    pad_x, pad_y = 12, 8
                    x0 = max(0, x - pad_x)
                    y0 = max(0, y - pad_y)
                    x1 = min(frame.shape[1], x + w + pad_x)
                    y1 = min(frame.shape[0], y + h + pad_y)
                    crop = frame[y0:y1, x0:x1]

                    thumb_filename = f"prov_{counter}_{re.sub(r'[^a-zA-Z0-9]', '_', grounded_text)}.png"
                    thumb_path = self.provenance_dir / thumb_filename
                    cv2.imwrite(str(thumb_path), crop)
                    thumbnail_url = f"/api/timeline/provenance/thumb/{thumb_filename}"
            except Exception:
                pass

        return WordAlignment(
            id=f"w_{counter}",
            word=grounded_text,
            start=start_t,
            end=end_t,
            confidence=0.95,
            is_technical=True,
            raw_asr_word=raw_phrase,
            provenance_frame_time=frame_time,
            provenance_bbox=bbox,
            provenance_thumbnail_url=thumbnail_url,
            phonetic_sim_score=round(sim_score, 3),
        )
