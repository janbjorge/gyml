"""
Tests for scalar values: strings, booleans, null, and numbers.

Each section covers the valid forms the spec allows and the invalid forms
it explicitly forbids.
"""

from __future__ import annotations

import math

from gyaml import loads

from .conftest import fail, ok_eq


# ===========================================================================
# Strings
# ===========================================================================


class TestStringsValid:
    def test_plain_simple(self):
        ok_eq("key: hello\n", {"key": "hello"})

    def test_plain_alphanumeric(self):
        ok_eq("key: abc123\n", {"key": "abc123"})

    def test_plain_with_underscore(self):
        ok_eq("key: foo_bar\n", {"key": "foo_bar"})

    def test_plain_with_hyphen(self):
        ok_eq("key: foo-bar\n", {"key": "foo-bar"})

    def test_plain_with_dot(self):
        ok_eq("key: foo.bar\n", {"key": "foo.bar"})

    def test_plain_with_slash(self):
        ok_eq("key: foo/bar\n", {"key": "foo/bar"})

    def test_double_quoted_simple(self):
        ok_eq('key: "hello world"\n', {"key": "hello world"})

    def test_double_quoted_empty(self):
        ok_eq('key: ""\n', {"key": ""})

    # Quoting disambiguates reserved words from their typed meanings.
    def test_double_quoted_reserved_true(self):
        ok_eq('key: "true"\n', {"key": "true"})

    def test_double_quoted_reserved_false(self):
        ok_eq('key: "false"\n', {"key": "false"})

    def test_double_quoted_reserved_null(self):
        ok_eq('key: "null"\n', {"key": "null"})

    def test_double_quoted_number_string(self):
        ok_eq('key: "42"\n', {"key": "42"})

    # JSON escape sequences.
    def test_escape_newline(self):
        ok_eq('key: "line1\\nline2"\n', {"key": "line1\nline2"})

    def test_escape_tab(self):
        ok_eq('key: "col1\\tcol2"\n', {"key": "col1\tcol2"})

    def test_escape_backslash(self):
        ok_eq('key: "a\\\\b"\n', {"key": "a\\b"})

    def test_escape_double_quote(self):
        ok_eq('key: "say \\"hi\\""\n', {"key": 'say "hi"'})

    def test_escape_slash(self):
        ok_eq('key: "a\\/b"\n', {"key": "a/b"})

    def test_escape_backspace(self):
        ok_eq('key: "\\b"\n', {"key": "\b"})

    def test_escape_formfeed(self):
        ok_eq('key: "\\f"\n', {"key": "\f"})

    def test_escape_carriage_return(self):
        ok_eq('key: "\\r"\n', {"key": "\r"})

    def test_escape_unicode(self):
        ok_eq('key: "\\u0041"\n', {"key": "A"})

    def test_escape_unicode_snowman(self):
        ok_eq('key: "\\u2603"\n', {"key": "\u2603"})

    def test_root_plain_string(self):
        ok_eq("hello\n", "hello")

    def test_root_quoted_string(self):
        ok_eq('"hello world"\n', "hello world")


class TestStringsInvalid:
    def test_single_quoted_value(self):
        fail("key: 'value'\n", "Single-quoted")

    def test_single_quoted_key(self):
        fail("'key': value\n", "Single-quoted")

    def test_unterminated_double_quote(self):
        fail('key: "unterminated\n', "Unterminated")

    def test_bad_escape_sequence(self):
        fail('key: "\\q"\n', "Unknown escape")

    def test_unicode_escape_too_short(self):
        fail('key: "\\u004"\n', "Invalid \\uXXXX")

    def test_unicode_escape_non_hex(self):
        fail('key: "\\uGGGG"\n', "Invalid \\uXXXX")


# ===========================================================================
# Booleans
# ===========================================================================


class TestBooleansValid:
    def test_true_value(self):
        ok_eq("key: true\n", {"key": True})

    def test_false_value(self):
        ok_eq("key: false\n", {"key": False})

    def test_root_true(self):
        ok_eq("true\n", True)

    def test_root_false(self):
        ok_eq("false\n", False)

    def test_true_is_bool_type(self):
        result = loads("key: true\n")
        assert isinstance(result, dict)
        assert type(result["key"]) is bool

    def test_false_is_bool_type(self):
        result = loads("key: false\n")
        assert isinstance(result, dict)
        assert type(result["key"]) is bool


class TestBooleansInvalid:
    # YAML 1.1 spellings that GYAML bans.
    def test_True_capital(self):
        fail("key: True\n", "not a valid boolean")

    def test_False_capital(self):
        fail("key: False\n", "not a valid boolean")

    def test_TRUE_all_caps(self):
        fail("key: TRUE\n", "not a valid boolean")

    def test_FALSE_all_caps(self):
        fail("key: FALSE\n", "not a valid boolean")

    def test_yes(self):
        fail("key: yes\n", "not a valid boolean")

    def test_no(self):
        fail("key: no\n", "not a valid boolean")

    def test_on(self):
        fail("key: on\n", "not a valid boolean")

    def test_off(self):
        fail("key: off\n", "not a valid boolean")

    def test_Yes(self):
        fail("key: Yes\n", "not a valid boolean")

    def test_YES(self):
        fail("key: YES\n", "not a valid boolean")

    def test_ON(self):
        fail("key: ON\n", "not a valid boolean")

    def test_OFF(self):
        fail("key: OFF\n", "not a valid boolean")


# ===========================================================================
# Null
# ===========================================================================


class TestNullValid:
    def test_null_value(self):
        ok_eq("key: null\n", {"key": None})

    def test_root_null(self):
        ok_eq("null\n", None)

    def test_null_is_none_type(self):
        result = loads("key: null\n")
        assert isinstance(result, dict)
        assert result["key"] is None


class TestNullInvalid:
    def test_tilde(self):
        fail("key: ~\n", "not a valid null")

    def test_Null_capital(self):
        fail("key: Null\n", "not a valid null")

    def test_NULL_all_caps(self):
        fail("key: NULL\n", "not a valid null")

    def test_bare_empty_value(self):
        fail("key:\n", "Bare empty value")

    def test_bare_empty_value_at_eof(self):
        fail("key:", "Bare empty value")


# ===========================================================================
# Numbers
# ===========================================================================


class TestNumbersValid:
    def test_zero(self):
        ok_eq("key: 0\n", {"key": 0})

    def test_positive_integer(self):
        ok_eq("key: 42\n", {"key": 42})

    def test_negative_integer(self):
        ok_eq("key: -7\n", {"key": -7})

    def test_float(self):
        ok_eq("key: 3.14\n", {"key": 3.14})

    def test_negative_float(self):
        ok_eq("key: -0.5\n", {"key": -0.5})

    def test_float_one_point_zero(self):
        ok_eq("key: 1.0\n", {"key": 1.0})

    def test_scientific_lowercase_e(self):
        ok_eq("key: 1.5e10\n", {"key": 1.5e10})

    def test_scientific_uppercase_e(self):
        ok_eq("key: 1.5E10\n", {"key": 1.5e10})

    def test_scientific_explicit_plus(self):
        ok_eq("key: 1.5e+3\n", {"key": 1.5e3})

    def test_scientific_explicit_minus(self):
        ok_eq("key: 1.5e-3\n", {"key": 1.5e-3})

    def test_negative_zero_integer(self):
        ok_eq("key: -0\n", {"key": 0})

    def test_negative_zero_float(self):
        result = loads("key: -0.0\n")
        assert isinstance(result, dict)
        assert result["key"] == 0.0

    def test_integer_has_int_type(self):
        result = loads("key: 42\n")
        assert isinstance(result, dict)
        assert type(result["key"]) is int

    def test_float_has_float_type(self):
        result = loads("key: 3.14\n")
        assert isinstance(result, dict)
        assert type(result["key"]) is float

    def test_scientific_integer_base(self):
        # No decimal point, but exponent notation → float.
        ok_eq("key: 2e3\n", {"key": 2000.0})

    def test_negative_scientific(self):
        result = loads("v: -1.5e-2\n")
        assert isinstance(result, dict)
        assert math.isclose(result["v"], -0.015)

    def test_large_integer(self):
        ok_eq("key: 9999999999999999\n", {"key": 9999999999999999})

    def test_root_integer(self):
        ok_eq("42\n", 42)

    def test_root_float(self):
        ok_eq("3.14\n", 3.14)


class TestNumbersInvalid:
    def test_leading_zeros(self):
        fail("key: 007\n", "leading zeros")

    def test_leading_zero_octal_look_alike(self):
        fail("key: 0123\n", "leading zeros")

    def test_leading_plus_integer(self):
        fail("key: +1\n", "leading plus")

    def test_leading_plus_float(self):
        fail("key: +1.5\n", "leading plus")

    def test_bare_leading_decimal(self):
        fail("key: .5\n", "write 0.5")

    def test_bare_trailing_decimal(self):
        fail("key: 1.\n", "write 0.5 or 1.0")

    def test_underscore_separator(self):
        fail("key: 1_000\n", "underscore")

    def test_hex_literal(self):
        fail("key: 0xFF\n", "hex/octal/binary")

    def test_octal_literal(self):
        fail("key: 0o77\n", "hex/octal/binary")

    def test_binary_literal(self):
        fail("key: 0b101\n", "hex/octal/binary")

    def test_inf(self):
        fail("key: .inf\n", ".inf/.nan")

    def test_negative_inf(self):
        fail("key: -.inf\n", ".inf/.nan")

    def test_nan(self):
        fail("key: .nan\n", ".inf/.nan")

    def test_INF_uppercase(self):
        fail("key: .INF\n", ".inf/.nan")

    def test_NaN_mixed_case(self):
        fail("key: .NaN\n", ".inf/.nan")
