"""
GYML value types and scalar coercion.

GValue is the closed set of Python types that a parsed GYML document can
produce — identical to what JSON can express:

    null   → None
    bool   → bool
    number → int | float
    string → str
    array  → list[GValue]
    object → dict[str, GValue]

coerce_scalar() converts a plain Token to the most specific GValue type,
following JSON semantics: quoted scalars are always strings; plain scalars
are matched against null, booleans, integers, and floats in that order.
"""

from __future__ import annotations

import re
from typing import Union

from gyml.tokens import ScalarStyle, Token


# The complete set of value types a GYML document can contain.
# Using a recursive Union instead of a TypeAlias makes the intent explicit.
GValue = Union[
    None,
    bool,
    int,
    float,
    str,
    "list[GValue]",
    "dict[str, GValue]",
]


# ---------------------------------------------------------------------------
# Patterns — used only for coercion, not validation (validation is in lexer.py)
# ---------------------------------------------------------------------------

_RE_VALID_INT: re.Pattern[str] = re.compile(r"^-?(0|[1-9]\d*)$")
_RE_VALID_FLOAT: re.Pattern[str] = re.compile(r"^-?(0|[1-9]\d*)\.\d+([eE][+\-]?\d+)?$")
_RE_VALID_SCI: re.Pattern[str] = re.compile(r"^-?(0|[1-9]\d*)[eE][+\-]?\d+$")


def coerce_scalar(token: Token) -> GValue:
    """
    Convert a validated SCALAR token to its Python value.

    Quoted scalars are always returned as strings — quoting is the explicit
    opt-out from type inference.

    Plain scalars are matched in this order:
      1. "null"  → None
      2. "true"  → True
      3. "false" → False
      4. integer pattern → int
      5. decimal float pattern → float
      6. scientific notation pattern → float
      7. anything else → str
    """
    if token.style == ScalarStyle.QUOTED:
        return token.value

    text = token.value

    if text == "null":
        return None
    if text == "true":
        return True
    if text == "false":
        return False
    if _RE_VALID_INT.match(text):
        return int(text)
    if _RE_VALID_FLOAT.match(text):
        return float(text)
    if _RE_VALID_SCI.match(text):
        return float(text)

    return text
