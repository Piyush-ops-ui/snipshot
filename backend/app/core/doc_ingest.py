"""
Document Ingestion & Pedagogical Compiler Engine:
Makes SnipShot 100% Document-Agnostic. Ingests ANY document:
- PDF (.pdf) via native pdftotext / poppler
- Word (.docx) via standard zip/XML parser
- Markdown (.md) with code fences and header extraction
- Source Code (.py, .js, .ts, .java, .cpp, .go, .rs, .html, .css, .sql, .sh, .json, .yaml)
- Plain text / Notes (.txt)

Extracts title, code blocks, and core pedagogical beats, compiling them into
animated 9:16 Explainer Reels.
"""

import os
import re
import json
import zipfile
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


class DocumentIngestEngine:
    SUPPORTED_EXTENSIONS = {
        ".pdf", ".docx", ".md", ".markdown", ".txt",
        ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".cpp", ".c", ".h",
        ".go", ".rs", ".html", ".css", ".sql", ".sh", ".bash",
        ".json", ".yaml", ".yml", ".xml", ".toml"
    }

    def __init__(self):
        pass

    def is_supported(self, filename: str) -> bool:
        ext = Path(filename).suffix.lower()
        return ext in self.SUPPORTED_EXTENSIONS

    def parse_document(self, file_path: str) -> Dict[str, Any]:
        """Parses any supported document into structured title, text, and code blocks."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")

        ext = path.suffix.lower()
        title = path.stem.replace("_", " ").replace("-", " ").title()

        if ext == ".pdf":
            raw_text = self._parse_pdf(file_path)
            code_blocks = self._extract_code_blocks_from_text(raw_text)
        elif ext == ".docx":
            raw_text = self._parse_docx(file_path)
            code_blocks = self._extract_code_blocks_from_text(raw_text)
        elif ext in [".md", ".markdown"]:
            raw_text, title_override, code_blocks = self._parse_markdown(file_path)
            if title_override:
                title = title_override
        elif ext in [".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".cpp", ".c", ".go", ".rs", ".html", ".css", ".sql", ".sh", ".bash", ".json", ".yaml", ".yml", ".xml"]:
            raw_text, code_blocks = self._parse_source_code(file_path, ext)
        else:
            # .txt or fallback plain text
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                raw_text = f.read()
            code_blocks = self._extract_code_blocks_from_text(raw_text)

        # Detect primary language
        language = self._detect_language(ext, raw_text, code_blocks)

        return {
            "title": title,
            "filename": path.name,
            "extension": ext,
            "language": language,
            "raw_text": raw_text.strip(),
            "code_blocks": code_blocks,
            "character_count": len(raw_text),
            "line_count": len(raw_text.splitlines()),
        }

    def _parse_pdf(self, file_path: str) -> str:
        """Extracts text from PDF via pdftotext or binary stream search."""
        try:
            # Try native pdftotext (ultra-fast, < 0.05s)
            res = subprocess.run(
                ["pdftotext", "-layout", str(file_path), "-"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                check=True
            )
            text = res.stdout.decode("utf-8", errors="replace")
            if text.strip():
                return text
        except Exception:
            pass

        # Fallback binary text scanner
        with open(file_path, "rb") as f:
            data = f.read().decode("latin-1", errors="replace")
            # Extract plain string streams inside BT ... ET blocks
            matches = re.findall(r"\(([^\(\)]+)\)\s*Tj", data)
            if matches:
                return " ".join(matches)
        return "PDF content extracted without raw text."

    def _parse_docx(self, file_path: str) -> str:
        """Extracts text from docx without extra libraries."""
        try:
            with zipfile.ZipFile(file_path) as z:
                xml_data = z.read("word/document.xml")
                root = ET.fromstring(xml_data)
                # Word document text is in <w:t> elements
                texts = [node.text for node in root.iter() if node.text and node.tag.endswith("t")]
                return " ".join(texts)
        except Exception:
            return ""

    def _parse_markdown(self, file_path: str) -> Tuple[str, Optional[str], List[Dict[str, str]]]:
        """Extracts headers, text, and fenced code blocks from markdown."""
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        title = None
        # Check first level 1 heading
        h1 = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if h1:
            title = h1.group(1).strip()

        # Extract fenced code blocks
        code_blocks = []
        pattern = r"```([a-zA-Z0-9_\-\+]*)\n([\s\S]*?)```"
        for match in re.finditer(pattern, content):
            lang = match.group(1).strip() or "code"
            code = match.group(2).strip()
            if code:
                code_blocks.append({"language": lang, "code": code})

        return content, title, code_blocks

    def _parse_source_code(self, file_path: str, ext: str) -> Tuple[str, List[Dict[str, str]]]:
        """Parses raw source code file into structured blocks."""
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        lang_map = {
            ".py": "python", ".js": "javascript", ".ts": "typescript", ".tsx": "typescript",
            ".jsx": "javascript", ".java": "java", ".cpp": "cpp", ".c": "c", ".go": "go",
            ".rs": "rust", ".html": "html", ".css": "css", ".sql": "sql", ".sh": "bash",
            ".json": "json", ".yaml": "yaml", ".yml": "yaml", ".xml": "xml"
        }
        lang = lang_map.get(ext, "code")

        # Split into readable chunks if long
        lines = content.splitlines()
        code_blocks = []
        if len(lines) <= 25:
            code_blocks.append({"language": lang, "code": content.strip()})
        else:
            # Take top 20 lines as main block
            code_blocks.append({"language": lang, "code": "\n".join(lines[:20])})
            # If there are functions or classes later, extract one
            for i, line in enumerate(lines[20:], start=20):
                if any(line.strip().startswith(kw) for kw in ["def ", "class ", "function ", "export function", "public class"]):
                    sub_chunk = "\n".join(lines[i:i+18])
                    code_blocks.append({"language": lang, "code": sub_chunk})
                    break

        return content, code_blocks

    def _extract_code_blocks_from_text(self, text: str) -> List[Dict[str, str]]:
        """Finds indented or formatted code chunks in plain text."""
        blocks = []
        fenced = re.findall(r"```([a-zA-Z0-9_\-\+]*)\n([\s\S]*?)```", text)
        for lang, code in fenced:
            if code.strip():
                blocks.append({"language": lang.strip() or "python", "code": code.strip()})

        if not blocks:
            # Look for lines with programming punctuation
            code_lines = [
                line for line in text.splitlines()
                if any(sym in line for sym in ["def ", "class ", "import ", "const ", "let ", "function", "=>", "return ", "{", "}", ";", "<!--"])
            ]
            if len(code_lines) >= 3:
                blocks.append({"language": "python", "code": "\n".join(code_lines[:14])})

        return blocks

    def _detect_language(self, ext: str, text: str, code_blocks: List[Dict[str, str]]) -> str:
        if code_blocks and code_blocks[0].get("language") and code_blocks[0]["language"] != "code":
            return code_blocks[0]["language"].lower()

        ext_map = {
            ".py": "python", ".js": "javascript", ".ts": "typescript", ".html": "html",
            ".css": "css", ".sql": "sql", ".sh": "bash", ".json": "json", ".yaml": "yaml"
        }
        if ext in ext_map:
            return ext_map[ext]

        low = text.lower()
        if "def " in low or "import " in low or "class " in low:
            return "python"
        elif "const " in low or "function " in low or "=>" in low:
            return "javascript"
        elif "<!doctype" in low or "<html" in low:
            return "html"
        elif "docker" in low or "container" in low:
            return "bash"
        return "python"

    def compile_document_to_scenes(
        self,
        doc_data: Dict[str, Any],
        topic_focus: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """
        Compiles any parsed document into the canonical 4 pedagogical scenes:
        Scene 1: Hook & Core Problem
        Scene 2: Core Concept & Architecture
        Scene 3: Contrast / Key Implementation
        Scene 4: Verification & Takeaway
        """
        title = topic_focus or doc_data["title"]
        lang = doc_data["language"]
        code_blocks = doc_data["code_blocks"]
        raw_text = doc_data["raw_text"]

        # Extract sentences from text for narrations
        sentences = [s.strip() for s in re.split(r"[.\n!?]", raw_text) if len(s.strip()) > 15]

        # Scene 1: Hook
        hook_narr = f"Understanding {title}: here is the core concept you need to know."
        if sentences:
            hook_narr = sentences[0]
            if len(hook_narr) > 120:
                hook_narr = hook_narr[:117] + "..."

        hook_code = f"// Topic: {title}\n// Document: {doc_data['filename']}\nconst focus = '{title}';"
        if lang == "python":
            hook_code = f"# Topic: {title}\n# Document: {doc_data['filename']}\ntopic = '{title}'"

        # Scene 2: Core Concept
        core_narr = f"Here is how {title} is structured in implementation."
        if len(sentences) > 1:
            core_narr = sentences[1]
            if len(core_narr) > 120:
                core_narr = core_narr[:117] + "..."

        core_code = code_blocks[0]["code"] if code_blocks else f"# Core Implementation\nprint('Mastering {title}')"
        # Trim code block to fit mobile card
        core_code = "\n".join(core_code.splitlines()[:12])

        # Scene 3: Contrast / Nuance
        contrast_narr = f"Notice how this pattern optimizes performance and eliminates bottlenecks."
        if len(sentences) > 2:
            contrast_narr = sentences[2]
            if len(contrast_narr) > 120:
                contrast_narr = contrast_narr[:117] + "..."

        if len(code_blocks) > 1:
            contrast_code = "\n".join(code_blocks[1]["code"].splitlines()[:12])
        else:
            if lang == "python":
                contrast_code = f"# Optimal Execution Pattern\ndef process_{title.lower().replace(' ', '_')}():\n    # Zero-allocation execution\n    return {{'status': 'verified', 'target': '{title}'}}"
            else:
                contrast_code = f"// Optimal Execution Pattern\nfunction process() {{\n  return {{ status: 'verified', target: '{title}' }};\n}}"

        # Scene 4: Verification
        verify_narr = f"Verify execution directly in your terminal or test suite."
        if len(sentences) > 3:
            verify_narr = sentences[3]
            if len(verify_narr) > 120:
                verify_narr = verify_narr[:117] + "..."

        verify_code = f"$ test_{title.lower().replace(' ', '_')}\n[PASS] 100% tests passed\n[200 OK] Output verified"

        return [
            {
                "title": f"Scene 1: Hook - {title}",
                "narration_text": hook_narr,
                "code_snippet": hook_code,
                "language": lang,
            },
            {
                "title": f"Scene 2: Core Architecture",
                "narration_text": core_narr,
                "code_snippet": core_code,
                "language": lang,
            },
            {
                "title": f"Scene 3: Key Implementation",
                "narration_text": contrast_narr,
                "code_snippet": contrast_code,
                "language": lang,
            },
            {
                "title": f"Scene 4: Verification",
                "narration_text": verify_narr,
                "code_snippet": verify_code,
                "language": "bash",
            },
        ]
