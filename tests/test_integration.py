"""
Integration and edge-case tests.

These tests use realistic, composite documents and corner cases that span
multiple parser rules.  They complement the focused unit tests in the other
modules by exercising the parser end-to-end.
"""

from __future__ import annotations

import json
import math

from gyaml import loads

from .conftest import fail, ok, ok_eq


# ===========================================================================
# Realistic configuration documents
# ===========================================================================


class TestIntegration:
    def test_database_config(self):
        src = "database:\n  host: localhost\n  port: 5432\n  name: mydb\n  ssl: true\n"
        ok_eq(
            src,
            {
                "database": {
                    "host": "localhost",
                    "port": 5432,
                    "name": "mydb",
                    "ssl": True,
                }
            },
        )

    def test_server_config_with_list(self):
        src = (
            "server:\n"
            "  host: 0.0.0.0\n"
            "  port: 8080\n"
            "  workers: 4\n"
            "  debug: false\n"
            "  allowed_hosts:\n"
            "    - localhost\n"
            "    - 127.0.0.1\n"
        )
        ok_eq(
            src,
            {
                "server": {
                    "host": "0.0.0.0",
                    "port": 8080,
                    "workers": 4,
                    "debug": False,
                    "allowed_hosts": ["localhost", "127.0.0.1"],
                }
            },
        )

    def test_list_of_people(self):
        src = "-\n  name: Alice\n  age: 30\n-\n  name: Bob\n  age: 25\n"
        ok_eq(src, [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}])

    def test_nested_sequences_in_mapping(self):
        src = "matrix:\n  -\n    - 1\n    - 2\n  -\n    - 3\n    - 4\n"
        ok_eq(src, {"matrix": [[1, 2], [3, 4]]})

    def test_all_scalar_types_together(self):
        src = (
            "str_plain: hello\n"
            'str_quoted: "world"\n'
            "int_val: 42\n"
            "float_val: 3.14\n"
            "bool_t: true\n"
            "bool_f: false\n"
            "null_val: null\n"
        )
        result = loads(src)
        assert isinstance(result, dict)
        assert result["str_plain"] == "hello"
        assert result["str_quoted"] == "world"
        assert result["int_val"] == 42
        assert result["float_val"] == 3.14
        assert result["bool_t"] is True
        assert result["bool_f"] is False
        assert result["null_val"] is None

    def test_json_roundtrip(self):
        src = '"name": Alice\n"age": 30\n'
        result = loads(src)
        assert isinstance(result, dict)
        roundtripped = json.loads(json.dumps(result))
        assert roundtripped == {"name": "Alice", "age": 30}

    def test_deeply_nested_five_levels(self):
        src = "l1:\n  l2:\n    l3:\n      l4:\n        l5: deep\n"
        ok_eq(src, {"l1": {"l2": {"l3": {"l4": {"l5": "deep"}}}}})

    def test_empty_collections_as_values(self):
        src = "empty_map: {}\nempty_list: []\n"
        ok_eq(src, {"empty_map": {}, "empty_list": []})

    def test_comment_does_not_affect_value(self):
        src = "a: 1 # inline comment\nb: 2\n"
        ok_eq(src, {"a": 1, "b": 2})

    def test_sequence_with_mixed_flow_and_null(self):
        src = "- {}\n- []\n- null\n"
        ok_eq(src, [{}, [], None])

    def test_float_scientific_no_decimal(self):
        result = loads("v: 2e3\n")
        assert isinstance(result, dict)
        assert result["v"] == 2000.0
        assert type(result["v"]) is float

    def test_negative_scientific_float(self):
        result = loads("v: -1.5e-2\n")
        assert isinstance(result, dict)
        assert math.isclose(result["v"], -0.015)

    def test_quoted_key_with_colon(self):
        ok_eq('"host:port": val\n', {"host:port": "val"})

    def test_quoted_key_with_hash(self):
        ok_eq('"key#1": val\n', {"key#1": "val"})

    def test_version_string_stays_string(self):
        # Plain strings matching [a-zA-Z0-9_./-]+ remain strings even when
        # they look numeric (e.g. "1.2.3" has two dots, so it cannot be float).
        ok_eq("version: 1.2.3\n", {"version": "1.2.3"})

    def test_unix_path_value(self):
        ok_eq("path: /usr/local/bin\n", {"path": "/usr/local/bin"})

    def test_first_error_terminates_parsing(self):
        err = fail("key: ~\n", "not a valid null")
        assert err.line == 1

    def test_parse_error_has_line_and_col(self):
        err = fail("key: ~\n")
        assert err.line >= 1
        assert err.col >= 1

    def test_deep_sequence_of_mappings(self):
        src = "data:\n  -\n    x: 1\n    y: 2\n  -\n    x: 3\n    y: 4\n"
        ok_eq(src, {"data": [{"x": 1, "y": 2}, {"x": 3, "y": 4}]})

    def test_unicode_escape_in_value(self):
        ok_eq('key: "\\u00e9"\n', {"key": "\u00e9"})

    def test_plain_string_with_leading_digit(self):
        # Starts with letter — stays as string despite containing digits.
        ok_eq("key: v1\n", {"key": "v1"})

    def test_inline_comment_after_multiple_keys(self):
        ok_eq("a: 1 # comment\nb: 2 # comment\n", {"a": 1, "b": 2})


# ===========================================================================
# Edge cases and boundary conditions
# ===========================================================================


class TestEdgeCases:
    def test_empty_string_parses_as_null(self):
        ok_eq("", None)

    def test_only_newlines_parses_as_null(self):
        ok_eq("\n\n", None)

    def test_root_zero(self):
        ok_eq("0\n", 0)

    def test_root_negative_integer(self):
        ok_eq("-1\n", -1)

    def test_root_empty_map_no_newline(self):
        ok_eq("{}", {})

    def test_root_empty_list_no_newline(self):
        ok_eq("[]", [])

    def test_no_trailing_newline_scalar(self):
        ok_eq("42", 42)

    def test_no_trailing_newline_mapping(self):
        ok_eq("a: 1", {"a": 1})

    def test_no_trailing_newline_sequence(self):
        ok_eq("- 1\n- 2", [1, 2])

    def test_single_key_no_trailing_newline(self):
        ok_eq("key: val", {"key": "val"})

    def test_comment_with_many_leading_spaces(self):
        # Spaces before the comment marker should not leak into the value.
        ok_eq("key: val   # lots of spaces before comment\n", {"key": "val"})

    def test_large_integer(self):
        ok_eq("key: 9999999999999999\n", {"key": 9999999999999999})

    def test_single_item_sequence(self):
        ok_eq("- hello\n", ["hello"])

    def test_single_key_mapping(self):
        ok_eq("k: v\n", {"k": "v"})

    def test_mapping_value_is_empty_list(self):
        ok_eq("k: []\n", {"k": []})

    def test_mapping_value_is_empty_map(self):
        ok_eq("k: {}\n", {"k": {}})

    def test_sequence_item_is_empty_list(self):
        ok_eq("- []\n", [[]])

    def test_sequence_item_is_empty_map(self):
        ok_eq("- {}\n", [{}])

    def test_zero_float(self):
        result = loads("key: 0.0\n")
        assert isinstance(result, dict)
        assert result["key"] == 0.0
        assert type(result["key"]) is float

    def test_plain_string_version_with_dots(self):
        # Two dots prevent float parsing; result is a plain string.
        ok_eq("key: 1.2.3\n", {"key": "1.2.3"})
