"""
Unit tests for Tree-Sitter Syntax & Mobile Legibility Gate.
"""

from backend.app.core.tree_sitter_gate import TreeSitterGate


def test_valid_python_syntax():
    gate = TreeSitterGate()
    code = "def add(a: int, b: int) -> int:\n    return a + b"
    result = gate.validate_snippet(code, language="python")
    assert result.is_valid is True
    assert len(result.syntax_errors) == 0
    assert result.max_line_width <= 42


def test_syntax_error_detection():
    gate = TreeSitterGate()
    broken_code = "def broken_func(\n    return 42"
    result = gate.validate_snippet(broken_code, language="python")
    assert result.is_valid is False
    assert len(result.syntax_errors) > 0


def test_line_length_violation_and_reflow():
    gate = TreeSitterGate(max_line_width=42)
    long_line_code = "result = process_data(user_id, account_type, authentication_token, session_id)"
    result = gate.validate_snippet(long_line_code, language="python")
    
    assert result.is_valid is False
    assert result.max_line_width > 42
    assert 0 in result.violating_line_indices

    # Test auto-reflow
    reflowed = gate.reflow_code(long_line_code, language="python")
    reflow_result = gate.validate_snippet(reflowed, language="python")
    assert reflow_result.max_line_width <= 42
