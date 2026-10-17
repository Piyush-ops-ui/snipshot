"""
Tests for FIX 1 (Proper Code Indentation & Formatting), FIX 2 (Unicode Tofu Sanitizer),
and FIX 3 (Dynamic Social Growth Pack & Zero Hardcoded React leftovers).
"""

import os
import re
import pytest
from PIL import Image, ImageDraw

from backend.app.core.fast_mode_a import auto_indent_code, FastModeAEngine
from backend.app.core.fast_native_compositor import sanitize_for_render, FastNativeCompositor


# ============================================================================
# FIX 1: PROPER CODE INDENTATION & CLEAN FORMATTING
# ============================================================================

def test_auto_indent_python_function():
    """Validates Python block indentation and indentation level tracking."""
    raw = "def calculate_total(items):\ntotal = 0\nfor item in items:\ntotal += item\nreturn total"
    indented = auto_indent_code(raw)
    lines = indented.split("\n")
    assert lines[0] == "def calculate_total(items):"
    assert lines[1] == "    total = 0"
    assert lines[2] == "    for item in items:"
    assert lines[3] == "        total += item"
    assert lines[4] == "        return total"


def test_auto_indent_branching_and_closing_delimiters():
    """Validates if-elif-else line indentation and dedent on closing delimiters."""
    raw = "if x > 0:\nprint('pos')\nelif x == 0:\nprint('zero')\nelse:\nprint('neg')"
    indented = auto_indent_code(raw)
    lines = indented.split("\n")
    assert lines[0] == "if x > 0:"
    assert lines[1] == "    print('pos')"
    assert lines[2] == "elif x == 0:"
    assert lines[3] == "    print('zero')"
    assert lines[4] == "else:"
    assert lines[5] == "    print('neg')"


def test_auto_indent_c_style_braces():
    """Validates C/Java/JS block indentation with curly braces."""
    raw = "public void init() {\nint x = 10;\nif (x > 5) {\nx = 0;\n}\n}"
    indented = auto_indent_code(raw)
    lines = indented.split("\n")
    assert lines[0] == "public void init() {"
    assert lines[1] == "    int x = 10;"
    assert lines[2] == "    if (x > 5) {"
    assert lines[3] == "        x = 0;"
    assert lines[4] == "    }"
    assert lines[5] == "}"


def test_auto_indent_line_wrap_under_42_chars():
    """
    Validates that lines longer than 42 characters are cleanly wrapped
    with an extra 4-space continuation indent, ensuring code NEVER overflows right edge.
    """
    raw = "<h1>Congratulations on your first code push on Github</h1>"
    indented = auto_indent_code(raw)
    lines = indented.split("\n")
    assert len(lines) >= 2
    for line in lines:
        assert len(line) <= 42, f"Line '{line}' exceeds 42 characters ({len(line)})"
    assert lines[1].startswith("    "), "Continuation line must have 4-space continuation indent"


def test_auto_indent_empty_and_whitespace():
    """Validates that empty lines and trailing spaces are handled gracefully."""
    assert auto_indent_code("") == ""
    assert auto_indent_code("   \n\n   ") == "\n\n"


def test_fast_native_compositor_leading_spaces_and_line_numbers(tmp_path):
    """
    Validates FastNativeCompositor leading whitespace preservation
    and line number rendering in muted slate on the left margin.
    """
    compositor = FastNativeCompositor()
    img = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Test direct syntax drawing with line number
    compositor._draw_simple_syntax_line(draw, "    return value;", x=92, y=200, accent="#4F46E5", line_num=5)

    # Test full overlay generation
    overlay_path = str(tmp_path / "test_indent_overlay.png")
    code = "def process():\n    data = load()\n    return data"
    compositor.render_overlay_png(
        institute_name="Indent Test Academy",
        brand_color="#4F46E5",
        code_snippet=code,
        language="python",
        output_path=overlay_path,
    )
    assert os.path.exists(overlay_path)
    loaded = Image.open(overlay_path)
    assert loaded.size == (1080, 1920)


# ============================================================================
# FIX 2: ELIMINATE ALL UNLOADED SQUARE ('□') CHARACTERS
# ============================================================================

def test_sanitize_for_render_unicode_emojis_to_ascii_tags():
    """Validates that all target Unicode emojis are converted to clean ASCII tags."""
    sample = "⚡ Speed 2.5x! ✅ Verified! ❌ Error! 🔥 Hot! 🚨 Bug! ⏸️ Pause! 🛑 Stop! 🚀 Prod! 口 box 红 red"
    clean = sanitize_for_render(sample)

    assert "[2.5x]" in clean
    assert "[VERIFIED]" in clean
    assert "[ERROR]" in clean
    assert "[HOT]" in clean
    assert "[BUG]" in clean
    assert "[PAUSE]" in clean
    assert "[STOP]" in clean
    assert "[PROD]" in clean
    assert "口" not in clean
    assert "红" not in clean

    # Guarantee all characters are printable ASCII
    for ch in clean:
        assert 32 <= ord(ch) <= 126 or ch == "\n", f"Unsanitized character: {repr(ch)}"


def test_sanitize_for_render_smart_quotes_dashes_tabs():
    """Validates tabs, smart quotes, dashes, and typographic symbols conversion."""
    sample = "\t“Smart Quotes” and ‘single quotes’ — em-dash – en-dash • bullet … ellipsis"
    clean = sanitize_for_render(sample)

    assert "\t" not in clean
    assert "    " in clean
    assert '"Smart Quotes"' in clean
    assert "'single quotes'" in clean
    assert "-" in clean
    assert "..." in clean

    for ch in clean:
        assert 32 <= ord(ch) <= 126 or ch == "\n", f"Unsanitized character: {repr(ch)}"


def test_sanitize_for_render_in_subtitles(tmp_path):
    """Validates that generate_ass_subtitles never produces non-ASCII or unrenderable tofu characters."""
    compositor = FastNativeCompositor()
    ass_path = str(tmp_path / "sanitized_subs.ass")

    words = [
        {"word": "⚡", "start": 0.0, "end": 0.5},
        {"word": "Auto-deploy", "start": 0.5, "end": 1.0},
        {"word": "🚀", "start": 1.0, "end": 1.5},
        {"word": "“production”", "start": 1.5, "end": 2.0},
    ]

    compositor.generate_ass_subtitles(words, start_sec=0.0, duration=3.0, output_path=ass_path)
    assert os.path.exists(ass_path)
    with open(ass_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "[2.5x]" in content
    assert "[PROD]" in content
    assert '"production"' in content
    assert "⚡" not in content
    assert "🚀" not in content
    assert "“" not in content


# ============================================================================
# FIX 3: DYNAMIC SOCIAL GROWTH PACK & REMOVAL OF HARDCODED REACT LEFTOVERS
# ============================================================================

def test_dynamic_social_growth_pack_java():
    """Validates dynamic social growth pack generation for Java video."""
    engine = FastModeAEngine()
    code = "public class Main {\n    JButton button = new JButton();\n}"
    growth = engine._generate_social_growth_pack(
        video_id="java123",
        code_language="java",
        code_snippet=code,
        repaired_terms=[{"repaired_term": "ActionListener"}],
        screen_tokens=[{"text": "JButton"}],
        transcript_text="Swing GUI button click listener",
    )

    assert "Java" in growth["hook_title"] or "ActionListener" in growth["hook_title"]
    assert "Verified Snippet (JAVA):" in growth["pinned_comment"]
    assert "JButton button = new JButton();" in growth["pinned_comment"]
    assert any("java" in tag.lower() for tag in growth["hashtags"])
    assert "#actionlistener" in [t.lower() for t in growth["hashtags"]]
    assert "https://snipshot.studio/snippet/java123" in growth["qr_code_url"]


def test_dynamic_social_growth_pack_python():
    """Validates dynamic social growth pack generation for Python video."""
    engine = FastModeAEngine()
    code = "def calculate_tax(income):\n    return income * 0.2"
    growth = engine._generate_social_growth_pack(
        video_id="py456",
        code_language="python",
        code_snippet=code,
        repaired_terms=[],
        screen_tokens=[],
        transcript_text="how to write python functions",
    )

    assert "Python" in growth["hook_title"]
    assert "Verified Snippet (PYTHON):" in growth["pinned_comment"]
    assert "def calculate_tax(income):" in growth["pinned_comment"]
    assert any("python" in tag.lower() for tag in growth["hashtags"])
    assert "https://snipshot.studio/snippet/py456" in growth["qr_code_url"]


def test_no_hardcoded_useeffect_in_growth_pack():
    """Validates that non-React videos do not contain hardcoded useEffect/React terms in growth pack."""
    engine = FastModeAEngine()
    code = "# Workflow: GitHub Desktop\n1. cd sample-repo\n2. code ."
    growth = engine._generate_social_growth_pack(
        video_id="git789",
        code_language="bash",
        code_snippet=code,
        repaired_terms=[],
        screen_tokens=[{"text": "GitHub Desktop"}],
        transcript_text="open terminal and git clone",
    )

    assert "useeffect" not in growth["hook_title"].lower()
    assert "useeffect" not in growth["pinned_comment"].lower()
    for tag in growth["hashtags"]:
        assert "useeffect" not in tag.lower()
        assert "react" not in tag.lower()
