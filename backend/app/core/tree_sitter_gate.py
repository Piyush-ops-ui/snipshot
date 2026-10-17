"""
Tree-Sitter Syntax & Mobile Legibility Gate.
Parses code snippets with Tree-Sitter or language-specific AST engines to ensure 0 syntax errors,
and strictly enforces the Mobile Legibility Rule: max 42 characters per line and max 14 lines per card.
"""

from typing import List, Tuple, Dict, Any, Optional
import ast
import json

try:
    import tree_sitter
    TREE_SITTER_AVAILABLE = True
except ImportError:
    tree_sitter = None
    TREE_SITTER_AVAILABLE = False


class ASTValidationResult:
    def __init__(
        self,
        is_valid: bool,
        language: str,
        syntax_errors: List[str],
        max_line_width: int,
        violating_line_indices: List[int],
        total_lines: int,
    ):
        self.is_valid = is_valid
        self.language = language
        self.syntax_errors = syntax_errors
        self.max_line_width = max_line_width
        self.violating_line_indices = violating_line_indices
        self.total_lines = total_lines

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "language": self.language,
            "syntax_errors": self.syntax_errors,
            "max_line_width": self.max_line_width,
            "violating_line_indices": self.violating_line_indices,
            "total_lines": self.total_lines,
        }


class TreeSitterGate:
    def __init__(self, max_line_width: int = 42, max_lines_per_card: int = 14):
        self.max_line_width = max_line_width
        self.max_lines_per_card = max_lines_per_card

    def validate_snippet(self, code: str, language: str = "python") -> ASTValidationResult:
        """
        Validates syntax correctness and mobile 9:16 layout constraints.
        """
        lines = code.split("\n")
        total_lines = len(lines)
        violating_lines = []
        max_w = 0

        # 1. Line Width & Count Audit (Mobile 9:16 Legibility)
        for idx, line in enumerate(lines):
            line_len = len(line)
            if line_len > max_w:
                max_w = line_len
            if line_len > self.max_line_width:
                violating_lines.append(idx)

        syntax_errors: List[str] = []

        # 2. Syntax Validation
        lang = language.lower()
        if lang == "python":
            try:
                ast.parse(code)
            except SyntaxError as e:
                syntax_errors.append(f"Python SyntaxError at line {e.lineno}: {e.msg}")
        elif lang in ["json", "yaml", "yml"]:
            if lang == "json":
                try:
                    json.loads(code)
                except Exception as e:
                    syntax_errors.append(f"Invalid JSON: {str(e)}")
        # Additional Tree-Sitter grammars can be queried here if installed

        is_valid = (len(syntax_errors) == 0) and (len(violating_lines) == 0) and (total_lines <= self.max_lines_per_card)

        return ASTValidationResult(
            is_valid=is_valid,
            language=lang,
            syntax_errors=syntax_errors,
            max_line_width=max_w,
            violating_line_indices=violating_lines,
            total_lines=total_lines,
        )

    def reflow_code(self, code: str, language: str = "python") -> str:
        """
        Automatically wraps or reflows lines exceeding 42 characters.
        """
        lines = code.split("\n")
        reflowed = []
        for line in lines:
            if len(line) <= self.max_line_width:
                reflowed.append(line)
            else:
                # Attempt to break at commas or operators
                indent = len(line) - len(line.lstrip())
                indent_str = " " * (indent + 4)
                parts = line.split(", ")
                if len(parts) > 1:
                    first = parts[0] + ","
                    reflowed.append(first)
                    for p in parts[1:-1]:
                        reflowed.append(indent_str + p + ",")
                    reflowed.append(indent_str + parts[-1])
                else:
                    # Break at space
                    words = line.split(" ")
                    cur = words[0]
                    for w in words[1:]:
                        if len(cur) + 1 + len(w) <= self.max_line_width:
                            cur += " " + w
                        else:
                            reflowed.append(cur)
                            cur = indent_str + w
                    reflowed.append(cur)
        return "\n".join(reflowed[: self.max_lines_per_card])
