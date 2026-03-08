"""
GYML — JSON semantics, YAML block syntax.

Public API
----------
loads(text)   Parse a GYML string and return a Python value.
load(path)    Parse a GYML file and return a Python value.

ParseError    Raised on the first syntax or semantic violation.
GValue        The set of Python types a parsed document can contain.

Package layout
--------------
  errors.py   ParseError
  tokens.py   TokenType, ScalarStyle, Token
  values.py   GValue, coerce_scalar()
  lexer.py    Lexer  — text → list[Token]
  parser.py   Parser — list[Token] → GValue
"""

from __future__ import annotations

from pathlib import Path

from gyml.errors import ParseError
from gyml.lexer import Lexer
from gyml.parser import Parser
from gyml.values import GValue


def loads(text: str) -> GValue:
    """
    Parse a GYML document from the string *text*.

    Raises
    ------
    ParseError
        On the first syntax or semantic violation found in the document.
    """
    tokens = Lexer(text).tokenize()
    return Parser(tokens).parse()


def load(path: str | Path) -> GValue:
    """
    Parse a GYML document from the file at *path*.

    Raises
    ------
    ParseError
        On the first syntax or semantic violation found in the document.
    OSError
        If the file cannot be opened or read.
    """
    return loads(Path(path).read_text(encoding="utf-8"))


__all__ = [
    "GValue",
    "ParseError",
    "load",
    "loads",
]


# ---------------------------------------------------------------------------
# CLI entry point — registered as `gyml` console script in pyproject.toml
# and also runnable as `python -m gyml <file.gyml>`.
# ---------------------------------------------------------------------------


def _cli() -> None:
    """
    Convert a GYML file to pretty-printed JSON and write it to stdout.

    Usage: gyml <file.gyml>
    """
    import json
    import sys

    if len(sys.argv) < 2:
        print("Usage: gyml <file.gyml>", file=sys.stderr)
        sys.exit(1)

    try:
        result = load(sys.argv[1])
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except ParseError as exc:
        print(f"Parse error: {exc}", file=sys.stderr)
        sys.exit(1)
    except OSError as exc:
        print(f"File error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    _cli()
