"""
Token types produced by the lexer and consumed by the parser.

TokenType  — the kind of structural element a token represents.
ScalarStyle — how a scalar was written in the source (plain or double-quoted).
Token       — a single lexed unit carrying its type, raw value, style, and
               source location.

Only SCALAR tokens carry a meaningful value and style; all other tokens
set value to "" and style to None.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    """Every distinct token kind the lexer can produce."""

    SCALAR = auto()  # a bare or double-quoted scalar value
    COLON = auto()  # ": " — the key/value separator
    DASH = auto()  # "- " — a sequence item marker
    LBRACE = auto()  # "{" — opens an empty mapping
    RBRACE = auto()  # "}" — closes an empty mapping
    LBRACKET = auto()  # "[" — opens an empty sequence
    RBRACKET = auto()  # "]" — closes an empty sequence
    NEWLINE = auto()  # end of a non-blank, non-comment line
    INDENT = auto()  # indentation increased by exactly 2 spaces
    DEDENT = auto()  # indentation decreased back to a previous level
    EOF = auto()  # end of the token stream


class ScalarStyle(Enum):
    """How a scalar was written in the source text."""

    PLAIN = auto()  # unquoted:  hello, true, 42
    QUOTED = auto()  # double-quoted: "hello world"


@dataclass(frozen=True)
class Token:
    """
    A single lexed unit.

    Attributes
    ----------
    type:
        The structural kind of this token.
    value:
        The decoded text content.  Non-empty only for SCALAR tokens; empty
        string for all structural tokens (COLON, DASH, braces, …).
    style:
        How the scalar was written.  None for non-SCALAR tokens.
    line:
        1-based line number in the source.
    col:
        1-based column number in the source.
    """

    type: TokenType
    value: str
    style: ScalarStyle | None
    line: int
    col: int

    def __repr__(self) -> str:
        if self.type == TokenType.SCALAR:
            # style is always set for SCALAR tokens
            assert self.style is not None
            return (
                f"Token(SCALAR {self.value!r}"
                f" {self.style.name}"
                f" @{self.line}:{self.col})"
            )
        return f"Token({self.type.name} @{self.line}:{self.col})"
