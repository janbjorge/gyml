"""
GYML Lexer — converts a raw source string into a flat list of Tokens.

Responsibilities
----------------
- Strip blank lines and comments.
- Enforce tab-free, even-numbered indentation and emit INDENT / DEDENT tokens
  so the parser never has to think about column numbers.
- Recognise every structural character: ":", "-", "{", "}", "[", "]".
- Read plain and double-quoted scalars.
- Validate plain scalars at lex time: reject loose booleans, loose nulls,
  bad number forms, anchors, aliases, and tags.

The lexer does NOT interpret values — it produces raw text.  Coercion
(string → int, string → bool, …) is the parser's job.
"""

from __future__ import annotations

import re
from typing import Final

from gyml.errors import ParseError
from gyml.tokens import ScalarStyle, Token, TokenType
from gyml.values import LOOSE_BOOLS, LOOSE_NULLS

# ---------------------------------------------------------------------------
# Compiled regular expressions used by the validator
# ---------------------------------------------------------------------------

# Patterns that identify *forbidden* number shapes.
_RE_LEADING_ZERO: Final = re.compile(r"^-?0\d+")
_RE_HEX_OCT_BIN: Final = re.compile(r"^-?0[xXoObB]")
_RE_SPECIAL_FLOAT: Final = re.compile(r"^[-+]?\.(inf|nan)$", re.IGNORECASE)
_RE_BARE_DECIMAL: Final = re.compile(r"^\.\d+$|^\d+\.$")
_RE_LEADING_PLUS: Final = re.compile(r"^\+")
_RE_UNDERSCORE: Final = re.compile(r"^-?\d[\d_]*_\d")

# ---------------------------------------------------------------------------
# Escape-sequence lookup table (hoisted out of the hot loop)
# ---------------------------------------------------------------------------

_SIMPLE_ESCAPES: Final[dict[str, str]] = {
    "n": "\n",
    "t": "\t",
    '"': '"',
    "\\": "\\",
    "/": "/",
    "b": "\b",
    "f": "\f",
    "r": "\r",
}


# ---------------------------------------------------------------------------
# Lexer
# ---------------------------------------------------------------------------


class Lexer:
    """
    Converts a GYML source string into a flat list of Tokens.

    Usage::

        tokens = Lexer(src).tokenize()
    """

    def __init__(self, src: str) -> None:
        self._src = src
        self._indent_stack: list[int] = [0]
        self._tokens: list[Token] = []

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def tokenize(self) -> list[Token]:
        """Lex the entire source and return the complete token list."""
        lines = self._src.splitlines()
        for line_no, line in enumerate(lines, start=1):
            self._lex_line(line, line_no)

        # Emit trailing DEDENTs to close any open indent levels.
        last_line = len(lines)
        while len(self._indent_stack) > 1:
            self._indent_stack.pop()
            self._emit(TokenType.DEDENT, line=last_line)

        self._emit(TokenType.EOF, line=last_line + 1)
        return self._tokens

    # ------------------------------------------------------------------
    # Line-level processing
    # ------------------------------------------------------------------

    def _lex_line(self, raw: str, line_no: int) -> None:
        """Process one source line, emitting tokens for its content."""
        content = raw.rstrip("\r\n")

        # Skip blank lines and comment-only lines entirely.
        stripped = content.lstrip()
        if not stripped or stripped.startswith("#"):
            return

        indent = self._check_leading_whitespace(content, line_no)
        self._handle_indent_change(indent, line_no)

        pos = indent
        while pos < len(content):
            pos = self._lex_token(content, pos, line_no)

        self._emit(TokenType.NEWLINE, line=line_no)

    def _check_leading_whitespace(self, content: str, line_no: int) -> int:
        """
        Reject tabs in leading whitespace and odd indent widths.

        Returns the indent level (number of leading spaces) so that the
        caller does not need to recompute it.
        """
        leading = content[: len(content) - len(content.lstrip())]

        if "\t" in leading:
            raise ParseError("Tabs are not allowed for indentation", line_no, 1)

        indent = len(leading)
        if indent % 2 != 0:
            raise ParseError(
                f"Indentation must be a multiple of 2 spaces (got {indent})",
                line_no,
                1,
            )
        return indent

    def _handle_indent_change(self, indent: int, line_no: int) -> None:
        """Push an INDENT or emit DEDENT(s) when the indent level changes."""
        current = self._indent_stack[-1]

        if indent > current:
            self._indent_stack.append(indent)
            self._emit(TokenType.INDENT, line=line_no)

        elif indent < current:
            while self._indent_stack[-1] > indent:
                self._indent_stack.pop()
                self._emit(TokenType.DEDENT, line=line_no)

            if self._indent_stack[-1] != indent:
                raise ParseError(
                    f"Inconsistent dedent"
                    f" (got {indent}, expected {self._indent_stack[-1]})",
                    line_no,
                    1,
                )

    # ------------------------------------------------------------------
    # Token-level processing
    # ------------------------------------------------------------------

    def _lex_token(self, line: str, pos: int, line_no: int) -> int:
        """
        Consume one token starting at *pos* and return the new position.

        Each branch returns early so the flow reads as a clear decision
        table — one condition, one outcome.
        """
        ch = line[pos]
        col = pos + 1  # convert to 1-based column

        if ch == " ":
            return pos + 1

        if ch == "#":
            return len(line)  # rest of line is a comment

        if ch == ":" and self._is_followed_by_space_or_end(line, pos):
            self._emit(TokenType.COLON, line=line_no, col=col)
            return pos + 1

        if ch == "-" and self._is_followed_by_space_or_end(line, pos):
            self._emit(TokenType.DASH, line=line_no, col=col)
            # Consume the trailing space when present so the parser never
            # sees it.
            if pos + 1 < len(line) and line[pos + 1] == " ":
                return pos + 2
            return pos + 1

        if ch == "{":
            self._emit(TokenType.LBRACE, line=line_no, col=col)
            return pos + 1
        if ch == "}":
            self._emit(TokenType.RBRACE, line=line_no, col=col)
            return pos + 1
        if ch == "[":
            self._emit(TokenType.LBRACKET, line=line_no, col=col)
            return pos + 1
        if ch == "]":
            self._emit(TokenType.RBRACKET, line=line_no, col=col)
            return pos + 1

        if ch == '"':
            value, length = self._read_quoted(line, pos + 1, line_no, col)
            self._tokens.append(
                Token(TokenType.SCALAR, value, ScalarStyle.QUOTED, line_no, col)
            )
            return pos + 1 + length

        if ch == "'":
            raise ParseError(
                "Single-quoted strings are not allowed; use double quotes",
                line_no,
                col,
            )

        if ch == "&":
            raise ParseError("Anchors (&) are not allowed in GYML", line_no, col)

        if ch == "*":
            raise ParseError("Aliases (*) are not allowed in GYML", line_no, col)

        # Ban all YAML tags — both single-bang (!tag) and double-bang (!!tag).
        if ch == "!":
            raise ParseError("Tags (!) are not allowed in GYML", line_no, col)

        value, length = self._read_plain(line, pos)
        if value:
            self._validate_plain(value, line_no, col)
            self._tokens.append(
                Token(TokenType.SCALAR, value, ScalarStyle.PLAIN, line_no, col)
            )
        return pos + length

    @staticmethod
    def _is_followed_by_space_or_end(line: str, pos: int) -> bool:
        """Return True when pos+1 is past the end of the line or a space."""
        return pos + 1 >= len(line) or line[pos + 1] == " "

    # ------------------------------------------------------------------
    # Scalar readers
    # ------------------------------------------------------------------

    def _read_quoted(
        self,
        line: str,
        pos: int,
        line_no: int,
        col: int,
    ) -> tuple[str, int]:
        """
        Read a double-quoted scalar starting just after the opening quote.

        Returns the decoded value and the number of characters consumed
        (including the closing quote).

        All JSON escape sequences are supported: \\n \\t \\\\ \\" \\/ \\b
        \\f \\r \\uXXXX.
        """
        chars: list[str] = []
        start = pos

        while pos < len(line):
            ch = line[pos]

            if ch == '"':
                return "".join(chars), pos - start + 1

            if ch == "\\":
                pos += 1
                if pos >= len(line):
                    raise ParseError("Unexpected end of escape sequence", line_no, col)
                pos = self._decode_escape(line, pos, line_no, col, chars)
                continue

            chars.append(ch)
            pos += 1

        raise ParseError("Unterminated double-quoted string", line_no, col)

    @staticmethod
    def _decode_escape(
        line: str,
        pos: int,
        line_no: int,
        col: int,
        chars: list[str],
    ) -> int:
        """
        Decode one escape sequence starting at *pos* (the character after
        the backslash) and append the resulting character to *chars*.

        Returns the position just past the last consumed character.
        """
        esc = line[pos]

        if esc in _SIMPLE_ESCAPES:
            chars.append(_SIMPLE_ESCAPES[esc])
            return pos + 1

        if esc == "u":
            hex4 = line[pos + 1 : pos + 5]
            if not re.fullmatch(r"[0-9a-fA-F]{4}", hex4):
                raise ParseError(f"Invalid \\uXXXX escape: {hex4!r}", line_no, col)
            chars.append(chr(int(hex4, 16)))
            return pos + 5  # skip the 'u' + 4 hex digits

        raise ParseError(f"Unknown escape \\{esc}", line_no, col)

    @staticmethod
    def _read_plain(line: str, pos: int) -> tuple[str, int]:
        """
        Read a plain (unquoted) scalar starting at *pos*.

        Stops at a comment marker (#) or a colon that is followed by
        whitespace or end-of-line.  Trailing spaces are stripped.

        Returns the raw text and the number of source characters consumed
        (before the strip, so the caller advances past the whitespace).
        """
        start = pos
        while pos < len(line):
            ch = line[pos]
            if ch == "#":
                break
            if ch == ":" and (pos + 1 >= len(line) or line[pos + 1] == " "):
                break
            pos += 1
        value = line[start:pos].rstrip()
        return value, pos - start

    # ------------------------------------------------------------------
    # Plain-scalar validation
    # ------------------------------------------------------------------

    def _validate_plain(self, value: str, line_no: int, col: int) -> None:
        """
        Reject plain scalars that look like YAML-extended forms GYML bans.

        Checks are ordered from most specific (special floats) to less
        specific (underscore separators) so the first match produces the
        most precise error message.
        """
        if value in LOOSE_BOOLS:
            raise ParseError(
                f'"{value}" is not a valid boolean; use true or false',
                line_no,
                col,
            )
        if value in LOOSE_NULLS:
            raise ParseError(
                f'"{value}" is not a valid null; use null',
                line_no,
                col,
            )
        if _RE_SPECIAL_FLOAT.match(value):
            raise ParseError(
                f'"{value}" — .inf/.nan are not allowed',
                line_no,
                col,
            )
        if _RE_BARE_DECIMAL.match(value):
            raise ParseError(
                f'"{value}" — write 0.5 or 1.0, not .5 or 1.',
                line_no,
                col,
            )
        if _RE_HEX_OCT_BIN.match(value):
            raise ParseError(
                f'"{value}" — hex/octal/binary literals are not allowed',
                line_no,
                col,
            )
        if _RE_LEADING_ZERO.match(value):
            raise ParseError(
                f'"{value}" — leading zeros are not allowed',
                line_no,
                col,
            )
        if _RE_LEADING_PLUS.match(value):
            raise ParseError(
                f'"{value}" — leading plus sign is not allowed',
                line_no,
                col,
            )
        if _RE_UNDERSCORE.match(value):
            raise ParseError(
                f'"{value}" — underscore separators in numbers are not allowed',
                line_no,
                col,
            )

    # ------------------------------------------------------------------
    # Emit helper
    # ------------------------------------------------------------------

    def _emit(
        self,
        token_type: TokenType,
        line: int,
        col: int = 1,
    ) -> None:
        """Append a structural (non-scalar) token to the output list."""
        self._tokens.append(Token(token_type, "", None, line, col))
