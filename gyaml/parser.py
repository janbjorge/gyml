"""
GYAML Parser — recursive descent over a flat Token list.

The parser consumes the token stream produced by the Lexer and builds a
plain Python value tree (GValue).  It knows nothing about source text,
characters, or indentation numbers — all of that was resolved by the Lexer
into INDENT / DEDENT tokens.

Grammar (informal)
------------------
document      = value EOF
value         = empty-mapping
              | empty-sequence
              | mapping          (SCALAR followed by COLON)
              | sequence         (DASH)
              | scalar

mapping       = (key COLON value-after-colon)+
value-after-colon = inline-value NEWLINE
              | NEWLINE INDENT block-value DEDENT

block-value   = sequence | mapping

sequence      = (DASH sequence-item)+
sequence-item = NEWLINE INDENT block-value DEDENT
              | empty-mapping NEWLINE
              | empty-sequence NEWLINE
              | scalar NEWLINE

Key rules enforced here (not in the lexer)
------------------------------------------
- Boolean / null / numeric literals are forbidden as plain keys.
- Duplicate keys within the same mapping are a hard error.
- Compact sequence items ("- key: val" on one line) are forbidden.
- A bare "key:\n" with no following INDENT is forbidden.
"""

from __future__ import annotations

import re
from typing import Final

from gyaml.errors import ParseError
from gyaml.tokens import ScalarStyle, Token, TokenType
from gyaml.values import GValue, coerce_scalar


# ---------------------------------------------------------------------------
# Key-validation helpers
# ---------------------------------------------------------------------------

# A plain key that matches a full JSON number shape is forbidden.
_RE_BARE_NUMBER: Final = re.compile(r"^-?(0|[1-9]\d*)(\.\d+)?([eE][+\-]?\d+)?$")

# All boolean-like spellings (valid and loose) — none are allowed as bare keys.
_ALL_BOOL_SPELLINGS: Final[frozenset[str]] = frozenset(
    {
        "true",
        "false",
        "yes",
        "no",
        "on",
        "off",
        "Yes",
        "No",
        "On",
        "Off",
        "YES",
        "NO",
        "ON",
        "OFF",
        "True",
        "False",
        "TRUE",
        "FALSE",
    }
)

# All null-like spellings — none are allowed as bare keys.
_ALL_NULL_SPELLINGS: Final[frozenset[str]] = frozenset(
    {
        "null",
        "~",
        "Null",
        "NULL",
    }
)


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


class Parser:
    """
    Recursive-descent parser that converts a Token list into a GValue tree.

    Usage::

        value = Parser(tokens).parse()
    """

    def __init__(self, tokens: list[Token]) -> None:
        self._tokens = tokens
        self._pos = 0

    # ------------------------------------------------------------------
    # Token navigation
    # ------------------------------------------------------------------

    def _peek(self, offset: int = 0) -> Token:
        """Return the token at the current position plus *offset*, clamped to EOF."""
        index = self._pos + offset
        if index < len(self._tokens):
            return self._tokens[index]
        return self._tokens[-1]  # always EOF

    def _advance(self) -> Token:
        """Consume and return the current token."""
        token = self._tokens[self._pos]
        self._pos += 1
        return token

    def _expect(self, expected: TokenType) -> Token:
        """Consume the next token, raising ParseError if its type differs."""
        token = self._advance()
        if token.type != expected:
            raise ParseError(
                f"Expected {expected.name}, got {token.type.name}",
                token.line,
                token.col,
            )
        return token

    def _skip_newlines(self) -> None:
        """Discard consecutive NEWLINE tokens (blank lines between constructs)."""
        while self._peek().type == TokenType.NEWLINE:
            self._advance()

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    def parse(self) -> GValue:
        """Parse the full document and return its value."""
        self._skip_newlines()

        if self._peek().type == TokenType.EOF:
            return None  # empty document → JSON null

        value = self._parse_value()

        self._skip_newlines()

        remaining = self._peek()
        if remaining.type != TokenType.EOF:
            raise ParseError(
                "Unexpected token after document root",
                remaining.line,
                remaining.col,
            )

        return value

    # ------------------------------------------------------------------
    # Value dispatch
    # ------------------------------------------------------------------

    def _parse_value(self) -> GValue:
        """Dispatch to the appropriate sub-parser based on the lookahead token."""
        lookahead = self._peek()

        if lookahead.type == TokenType.LBRACE:
            return self._parse_empty_mapping()

        if lookahead.type == TokenType.LBRACKET:
            return self._parse_empty_sequence()

        if lookahead.type == TokenType.SCALAR:
            # A scalar followed by a colon opens a mapping.
            if self._peek(1).type == TokenType.COLON:
                return self._parse_mapping()
            return coerce_scalar(self._advance())

        if lookahead.type == TokenType.DASH:
            return self._parse_sequence()

        raise ParseError(
            f"Expected a value, got {lookahead.type.name}",
            lookahead.line,
            lookahead.col,
        )

    # ------------------------------------------------------------------
    # Mappings
    # ------------------------------------------------------------------

    def _parse_empty_mapping(self) -> dict[str, GValue]:
        """Parse the literal "{}" token pair."""
        self._expect(TokenType.LBRACE)
        self._expect(TokenType.RBRACE)
        return {}

    def _parse_mapping(self) -> dict[str, GValue]:
        """
        Parse a block mapping: one or more "key: value" pairs at the current
        indent level.  Stops when the next token is not a SCALAR+COLON pair.
        """
        result: dict[str, GValue] = {}
        seen: set[str] = set()

        while self._peek().type == TokenType.SCALAR:
            # Peek ahead: stop if this scalar is a value, not a key.
            if self._peek(1).type != TokenType.COLON:
                break

            key_token = self._peek()
            key = self._parse_key()
            self._expect(TokenType.COLON)

            if key in seen:
                raise ParseError(
                    f'Duplicate key: "{key}"',
                    key_token.line,
                    key_token.col,
                )
            seen.add(key)
            result[key] = self._parse_value_after_colon()

        return result

    def _parse_key(self) -> str:
        """
        Consume a SCALAR token and validate it as a mapping key.

        Quoted keys are accepted as-is.  Plain keys must not be boolean
        literals, null literals, or numeric literals.
        """
        token = self._expect(TokenType.SCALAR)
        text = token.value

        if text == "":
            raise ParseError("Empty keys are not allowed", token.line, token.col)

        if token.style == ScalarStyle.QUOTED:
            return text  # quoted → any content is a valid key

        if text in _ALL_BOOL_SPELLINGS:
            raise ParseError(
                f'"{text}": boolean literals are not allowed as keys',
                token.line,
                token.col,
            )
        if text in _ALL_NULL_SPELLINGS:
            raise ParseError(
                f'"{text}": null literals are not allowed as keys',
                token.line,
                token.col,
            )
        if _RE_BARE_NUMBER.match(text):
            raise ParseError(
                f'"{text}": numeric literals are not allowed as keys',
                token.line,
                token.col,
            )

        return text

    def _parse_value_after_colon(self) -> GValue:
        """
        Parse the value that follows a colon.

        Two legal shapes:
          • Inline:  "key: <scalar|{}|[]> NEWLINE"
          • Block:   "key:\n  INDENT <mapping|sequence> DEDENT"
        """
        lookahead = self._peek()

        # Inline value on the same line.
        if lookahead.type in (TokenType.SCALAR, TokenType.LBRACE, TokenType.LBRACKET):
            value = self._parse_value()
            self._expect(TokenType.NEWLINE)
            return value

        # Block value on the next (indented) lines.
        if lookahead.type == TokenType.NEWLINE:
            if self._peek(1).type != TokenType.INDENT:
                raise ParseError(
                    "Bare empty value is not allowed; write 'null' explicitly",
                    lookahead.line,
                    lookahead.col,
                )
            self._advance()  # consume NEWLINE
            self._advance()  # consume INDENT
            value = self._parse_block_value()
            self._expect(TokenType.DEDENT)
            return value

        raise ParseError(
            f"Expected a value after ':', got {lookahead.type.name}",
            lookahead.line,
            lookahead.col,
        )

    def _parse_block_value(self) -> GValue:
        """
        Parse either a mapping or a sequence at the current (indented) level.

        This is called after an INDENT has been consumed, so it sees the
        first content token of the indented block.
        """
        lookahead = self._peek()

        if lookahead.type == TokenType.DASH:
            return self._parse_sequence()

        if lookahead.type == TokenType.SCALAR and self._peek(1).type == TokenType.COLON:
            return self._parse_mapping()

        raise ParseError(
            f"Expected mapping or sequence after indent, got {lookahead.type.name}",
            lookahead.line,
            lookahead.col,
        )

    # ------------------------------------------------------------------
    # Sequences
    # ------------------------------------------------------------------

    def _parse_empty_sequence(self) -> list[GValue]:
        """Parse the literal "[]" token pair."""
        self._expect(TokenType.LBRACKET)
        self._expect(TokenType.RBRACKET)
        return []

    def _parse_sequence(self) -> list[GValue]:
        """
        Parse a block sequence: one or more "- <item>" entries at the current
        indent level.  Stops when the next token is not a DASH.
        """
        items: list[GValue] = []
        while self._peek().type == TokenType.DASH:
            self._advance()  # consume the DASH
            items.append(self._parse_sequence_item())
        return items

    def _parse_sequence_item(self) -> GValue:
        """
        Parse the value of a single sequence item.

        Four legal shapes (after the DASH has been consumed):
          • Block:        "-\n  INDENT <mapping|sequence> DEDENT"
          • Empty map:    "- {} NEWLINE"
          • Empty list:   "- [] NEWLINE"
          • Scalar:       "- <scalar> NEWLINE"
        """
        lookahead = self._peek()

        # Block item: the dash is alone on its line, value starts on next line.
        if lookahead.type == TokenType.NEWLINE:
            if self._peek(1).type != TokenType.INDENT:
                raise ParseError(
                    "Bare empty sequence item is not allowed",
                    lookahead.line,
                    lookahead.col,
                )
            self._advance()  # consume NEWLINE
            self._advance()  # consume INDENT
            value = self._parse_block_value()
            self._expect(TokenType.DEDENT)
            # The last key/value in the block already consumed its NEWLINE;
            # skip any blank lines that follow before the next DASH.
            self._skip_newlines()
            return value

        # Empty mapping literal on the same line as the dash.
        if lookahead.type == TokenType.LBRACE:
            value = self._parse_empty_mapping()
            self._expect(TokenType.NEWLINE)
            return value

        # Empty sequence literal on the same line as the dash.
        if lookahead.type == TokenType.LBRACKET:
            value = self._parse_empty_sequence()
            self._expect(TokenType.NEWLINE)
            return value

        # Compact mapping ("- key: val") is forbidden in GYAML.
        if lookahead.type == TokenType.SCALAR and self._peek(1).type == TokenType.COLON:
            raise ParseError(
                "Compact mapping in sequence item is not allowed;"
                " put the mapping on the next line after '-'",
                lookahead.line,
                lookahead.col,
            )

        # Plain scalar item.
        if lookahead.type == TokenType.SCALAR:
            value = coerce_scalar(self._advance())
            self._expect(TokenType.NEWLINE)
            return value

        raise ParseError(
            f"Expected sequence item value, got {lookahead.type.name}",
            lookahead.line,
            lookahead.col,
        )
