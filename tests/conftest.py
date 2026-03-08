"""
Shared test helpers, available to every test file via pytest's conftest
import mechanism — no explicit import needed in test modules.

ok(src)            — assert parses without error, return the value
ok_eq(src, value)  — assert parses and the result equals value
fail(src, *frags)  — assert raises ParseError; every fragment must appear
                     in the formatted error string
"""

from __future__ import annotations

import pytest

from gyaml import ParseError, loads
from gyaml.values import GValue


def ok(src: str) -> GValue:
    """Parse *src* and return the result; fail the test on ParseError."""
    return loads(src)


def ok_eq(src: str, expected: GValue) -> GValue:
    """Parse *src* and assert the result equals *expected*."""
    result = loads(src)
    assert result == expected, f"expected {expected!r}, got {result!r}"
    return result


def fail(src: str, *frags: str) -> ParseError:
    """
    Assert that parsing *src* raises ParseError.

    Each string in *frags* must appear somewhere in the formatted error
    message — use this to pin down which rule was violated without
    coupling tests to the exact wording.
    """
    with pytest.raises(ParseError) as exc_info:
        loads(src)
    err = exc_info.value
    msg = str(err)
    for frag in frags:
        assert frag in msg, f"expected {frag!r} in error {msg!r}"
    return err
