"""
Tests for mapping (dict) parsing.

Covers single and multiple key-value pairs, nested mappings, flow-empty
syntax, mixed value types, and the invalid forms GYAML forbids.
"""

from __future__ import annotations

from .conftest import fail, ok, ok_eq


# ===========================================================================
# Valid mappings
# ===========================================================================


class TestMappingsValid:
    def test_single_pair(self):
        ok_eq("a: 1\n", {"a": 1})

    def test_multiple_pairs(self):
        ok_eq("a: 1\nb: 2\nc: 3\n", {"a": 1, "b": 2, "c": 3})

    def test_nested_mapping(self):
        ok_eq("outer:\n  inner: val\n", {"outer": {"inner": "val"}})

    def test_deeply_nested_mapping(self):
        ok_eq(
            "a:\n  b:\n    c:\n      d: leaf\n",
            {"a": {"b": {"c": {"d": "leaf"}}}},
        )

    def test_empty_mapping_flow(self):
        # {} is the only allowed inline mapping form — it means "empty map".
        ok_eq("key: {}\n", {"key": {}})

    def test_root_empty_mapping_flow(self):
        ok_eq("{}\n", {})

    def test_string_and_integer_values(self):
        ok_eq(
            "host: localhost\nport: 5432\n",
            {"host": "localhost", "port": 5432},
        )

    def test_mixed_value_types(self):
        src = 'name: Alice\nage: 30\nactive: true\nnotes: ""\n'
        ok_eq(src, {"name": "Alice", "age": 30, "active": True, "notes": ""})

    def test_sibling_nested_mappings(self):
        src = "a:\n  x: 1\nb:\n  y: 2\n"
        ok_eq(src, {"a": {"x": 1}, "b": {"y": 2}})

    def test_blank_line_between_root_keys_is_allowed(self):
        # Blank lines between root-level mapping keys fold into one mapping.
        ok_eq("a: 1\n\nb: 2\n", {"a": 1, "b": 2})


# ===========================================================================
# Invalid mappings
# ===========================================================================


class TestMappingsInvalid:
    def test_non_empty_flow_mapping(self):
        # Only {} is allowed; {a: 1} (flow mapping with content) is forbidden.
        fail("key: {a: 1}\n")

    def test_duplicate_key_flat(self):
        fail("x: 1\nx: 2\n", "Duplicate key")

    def test_duplicate_key_nested(self):
        fail("outer:\n  k: 1\n  k: 2\n", "Duplicate key")

    def test_bare_empty_value(self):
        fail("key:\n", "Bare empty value")

    def test_odd_indent_step(self):
        # Indentation must be a multiple of 2; 3 spaces is forbidden.
        fail("a:\n   b: 1\n", "multiple of 2")

    def test_tab_indent(self):
        fail("a:\n\tb: 1\n", "Tabs")
