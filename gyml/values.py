"""
GYML value types, shared constants, and scalar coercion.

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

This module also hosts the canonical boolean/null spelling sets and
number-validation regexes so that the lexer and parser can import them
instead of each maintaining their own copies.
"""

from __future__ import annotations

import re
from typing import Final

from gyml.tokens import ScalarStyle, Token

# The complete set of value types a GYML document can contain.
GValue = None | bool | int | float | str | list["GValue"] | dict[str, "GValue"]


# ------------------------------------------------------------------
# Canonical boolean / null spelling sets
# ------------------------------------------------------------------

# The only boolean spellings GYML accepts as values.
VALID_BOOLS: Final[frozenset[str]] = frozenset({"true", "false"})

# YAML-legacy boolean spellings that GYML explicitly forbids as values.
LOOSE_BOOLS: Final[frozenset[str]] = frozenset(
    {
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

# Every boolean-like spelling — used by the parser to reject bare keys.
ALL_BOOL_SPELLINGS: Final[frozenset[str]] = VALID_BOOLS | LOOSE_BOOLS

# YAML-legacy null spellings that GYML explicitly forbids as values.
LOOSE_NULLS: Final[frozenset[str]] = frozenset({"~", "Null", "NULL"})

# Every null-like spelling — used by the parser to reject bare keys.
ALL_NULL_SPELLINGS: Final[frozenset[str]] = LOOSE_NULLS | frozenset({"null"})


# ------------------------------------------------------------------
# Number-validation patterns (shared by lexer and coercion)
# ------------------------------------------------------------------

RE_VALID_INT: Final[re.Pattern[str]] = re.compile(r"^-?(0|[1-9]\d*)$")
RE_VALID_FLOAT: Final[re.Pattern[str]] = re.compile(
    r"^-?(0|[1-9]\d*)\.\d+([eE][+\-]?\d+)?$"
)
RE_VALID_SCI: Final[re.Pattern[str]] = re.compile(r"^-?(0|[1-9]\d*)[eE][+\-]?\d+$")


# ------------------------------------------------------------------
# Scalar coercion
# ------------------------------------------------------------------


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
      5. float / scientific notation pattern → float
      6. anything else → str
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
    if RE_VALID_INT.match(text):
        return int(text)
    if RE_VALID_FLOAT.match(text) or RE_VALID_SCI.match(text):
        return float(text)

    return text
