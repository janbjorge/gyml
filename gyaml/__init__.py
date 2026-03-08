"""
GYAML — JSON semantics, YAML block syntax.

Public API
----------
loads(text)   Parse a GYAML string and return a Python value.
load(path)    Parse a GYAML file and return a Python value.

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

from gyaml.errors import ParseError
from gyaml.lexer import Lexer
from gyaml.parser import Parser
from gyaml.values import GValue


def loads(text: str) -> GValue:
    """
    Parse a GYAML document from the string *text*.

    Raises
    ------
    ParseError
        On the first syntax or semantic violation found in the document.
    """
    tokens = Lexer(text).tokenize()
    return Parser(tokens).parse()


def load(path: str | Path) -> GValue:
    """
    Parse a GYAML document from the file at *path*.

    Raises
    ------
    ParseError
        On the first syntax or semantic violation found in the document.
    OSError
        If the file cannot be opened or read.
    """
    return loads(Path(path).read_text(encoding="utf-8"))


__all__ = [
    "loads",
    "load",
    "ParseError",
    "GValue",
]


# ---------------------------------------------------------------------------
# CLI entry point — registered as `gyaml` console script in pyproject.toml
# and also runnable as `python -m gyaml <file.gyaml>`.
# ---------------------------------------------------------------------------


def _cli() -> None:
    """
    Convert a GYAML file to pretty-printed JSON and write it to stdout.

    Usage: gyaml <file.gyaml>
    """
    import json
    import sys

    if len(sys.argv) < 2:
        print("Usage: gyaml <file.gyaml>", file=sys.stderr)
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
