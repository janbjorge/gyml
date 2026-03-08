"""
Errors raised by the GYAML parser.

A single exception type carries everything a caller needs to produce a
helpful diagnostic: the human-readable message plus the exact source
location (1-based line and column).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ParseError(Exception):
    """Raised on the first syntax or semantic violation found in the source."""

    message: str
    line: int
    col: int

    def __str__(self) -> str:
        return f"line {self.line}, col {self.col}: {self.message}"
