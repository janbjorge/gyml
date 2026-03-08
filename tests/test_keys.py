"""
Tests for mapping key rules.

GYAML allows plain alphanumeric keys and double-quoted keys.
Boolean literals, null literals, and numeric literals are forbidden
as bare keys; single-quoted keys are rejected unconditionally.
Duplicate keys are always an error.
"""

from __future__ import annotations

from .conftest import fail, ok_eq

# ===========================================================================
# Valid keys
# ===========================================================================


class TestKeysValid:
    def test_plain_alphanumeric(self):
        ok_eq("host: localhost\n", {"host": "localhost"})

    def test_plain_with_underscore(self):
        ok_eq("my_key: val\n", {"my_key": "val"})

    def test_plain_with_hyphen(self):
        ok_eq("my-key: val\n", {"my-key": "val"})

    def test_double_quoted_with_space(self):
        ok_eq('"my key": val\n', {"my key": "val"})

    def test_double_quoted_numeric_string(self):
        # Quoting forces the key to stay a string even if it looks like a number.
        ok_eq('"404": not found\n', {"404": "not found"})

    def test_double_quoted_http_header(self):
        ok_eq('"x-forwarded-for": 1.2.3.4\n', {"x-forwarded-for": "1.2.3.4"})

    def test_double_quoted_boolean_string(self):
        # "true" quoted → string key, not a boolean.
        ok_eq('"true": val\n', {"true": "val"})

    def test_double_quoted_null_string(self):
        ok_eq('"null": val\n', {"null": "val"})


# ===========================================================================
# Invalid keys
# ===========================================================================


class TestKeysInvalid:
    def test_bare_true_key(self):
        fail("true: val\n", "boolean literals are not allowed as keys")

    def test_bare_false_key(self):
        fail("false: val\n", "boolean literals are not allowed as keys")

    def test_bare_null_key(self):
        fail("null: val\n", "null literals are not allowed as keys")

    def test_bare_integer_key(self):
        fail("404: not found\n", "numeric literals are not allowed as keys")

    def test_bare_float_key(self):
        fail("3.14: val\n", "numeric literals are not allowed as keys")

    def test_bare_negative_integer_key(self):
        fail("-1: val\n", "numeric literals are not allowed as keys")

    def test_single_quoted_key(self):
        fail("'key': val\n", "Single-quoted")

    def test_duplicate_plain_key(self):
        fail("a: 1\na: 2\n", "Duplicate key")

    def test_duplicate_quoted_and_plain_key(self):
        # "a" and a resolve to the same string — still a duplicate.
        fail('"a": 1\na: 2\n', "Duplicate key")

    def test_empty_bare_key(self):
        # A bare colon with no preceding identifier is not a valid key.
        fail(": val\n")
