"""
Unit tests for Phonetic-Visual Repair Engine (ScreenLex-ASR Pass 2).
"""

from backend.app.core.phonetic_repair import PhoneticVisualRepairer
from backend.app.schemas.tssg import ASRWord, ScreenToken


def test_phonetic_repair_use_effect(sample_screen_tokens, sample_asr_words):
    repairer = PhoneticVisualRepairer()
    repaired = repairer.repair_transcript(sample_asr_words, sample_screen_tokens)

    repaired_words = [w.word for w in repaired]
    
    # Assert 'use a fact' was merged into 'useEffect'
    assert "useEffect" in repaired_words
    assert "use" not in repaired_words
    assert "fact" not in repaired_words

    # Locate useEffect token and verify provenance metadata
    use_eff_token = next(w for w in repaired if w.word == "useEffect")
    assert use_eff_token.is_technical is True
    assert use_eff_token.raw_asr_word is not None
    assert "use" in use_eff_token.raw_asr_word
    assert use_eff_token.provenance_frame_time == 14.2
    assert use_eff_token.provenance_bbox == (120, 180, 240, 32)


def test_phonetic_repair_autowired(sample_screen_tokens, sample_asr_words):
    repairer = PhoneticVisualRepairer()
    repaired = repairer.repair_transcript(sample_asr_words, sample_screen_tokens)

    repaired_words = [w.word for w in repaired]

    # Assert 'auto wired' was merged into '@Autowired'
    assert "@Autowired" in repaired_words
    assert "auto" not in repaired_words
    assert "wired" not in repaired_words

    autowired_token = next(w for w in repaired if w.word == "@Autowired")
    assert autowired_token.is_technical is True
    assert autowired_token.provenance_frame_time == 14.5


def test_ordinary_words_untouched(sample_screen_tokens, sample_asr_words):
    repairer = PhoneticVisualRepairer()
    repaired = repairer.repair_transcript(sample_asr_words, sample_screen_tokens)

    repaired_words = [w.word for w in repaired]
    # Standard conversational words must be preserved
    assert "dekho" in repaired_words
    assert "jab" in repaired_words
    assert "hum" in repaired_words
    assert "mein" in repaired_words
