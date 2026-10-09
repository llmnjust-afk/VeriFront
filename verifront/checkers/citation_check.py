"""Citation existence + quoted-fragment matching for retrieval-style steps."""

from __future__ import annotations

from typing import Any, Dict, Optional


def _norm(text: str) -> str:
    return " ".join(text.split()).lower()


class CitationChecker:
    """references: {doc_id: source_text}. Output must contain
    `citations`: [{"doc_id": ..., "quote": ...}]. A retrieval step with zero
    citations fails (nothing verifiable was produced)."""

    def __init__(self, name: str, references: Dict[str, str]):
        self.name = name
        self.references = {k: _norm(v) for k, v in references.items()}

    def check(self, output: Any, context: Optional[Dict] = None):
        from .base import CheckerResult

        if not isinstance(output, dict):
            return CheckerResult(self.name, passed=False, details={"problems": ["output is not a dict"]})
        cites = output.get("citations") or []
        if not cites:
            return CheckerResult(self.name, passed=False, details={"problems": ["no citations produced"]})
        problems = []
        for i, c in enumerate(cites):
            if not isinstance(c, dict):
                problems.append(f"citation[{i}] is not a dict")
                continue
            doc_id = c.get("doc_id")
            if doc_id not in self.references:
                problems.append(f"citation[{i}] references unknown doc_id: {doc_id!r}")
                continue
            quote = c.get("quote") or ""
            if not quote.strip():
                problems.append(f"citation[{i}] has empty quote")
            elif _norm(quote) not in self.references[doc_id]:
                problems.append(f"citation[{i}] quote not found in source {doc_id!r}")
        return CheckerResult(self.name, passed=not problems, details={"problems": problems})
