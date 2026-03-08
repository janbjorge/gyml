"""
Tests for sequence (list) parsing.

Covers plain sequences, sequences nested under mapping keys, sequences of
mappings, sequences of sequences, mixed scalar types, and the invalid forms
GYAML forbids.
"""

from __future__ import annotations

from .conftest import fail, ok_eq


# ===========================================================================
# Valid sequences
# ===========================================================================


class TestSequencesValid:
    def test_simple_integer_sequence(self):
        ok_eq("- 1\n- 2\n- 3\n", [1, 2, 3])

    def test_sequence_of_strings(self):
        ok_eq("- foo\n- bar\n", ["foo", "bar"])

    def test_sequence_under_key(self):
        ok_eq("items:\n  - a\n  - b\n", {"items": ["a", "b"]})

    def test_empty_sequence_flow(self):
        # [] is the only allowed inline sequence form — it means "empty list".
        ok_eq("key: []\n", {"key": []})

    def test_root_empty_sequence_flow(self):
        ok_eq("[]\n", [])

    def test_sequence_of_mappings(self):
        src = (
            "people:\n"
            "  -\n"
            "    name: Alice\n"
            "    age: 30\n"
            "  -\n"
            "    name: Bob\n"
            "    age: 25\n"
        )
        ok_eq(
            src,
            {"people": [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]},
        )

    def test_sequence_of_sequences(self):
        src = "matrix:\n  -\n    - 1\n    - 2\n  -\n    - 3\n    - 4\n"
        ok_eq(src, {"matrix": [[1, 2], [3, 4]]})

    def test_sequence_mixed_scalars(self):
        ok_eq("- 1\n- 3.14\n- true\n- null\n", [1, 3.14, True, None])

    def test_sequence_of_empty_mappings(self):
        ok_eq("- {}\n- {}\n", [{}, {}])

    def test_sequence_of_empty_sequences(self):
        ok_eq("- []\n- []\n", [[], []])

    def test_single_item_sequence(self):
        ok_eq("- hello\n", ["hello"])


# ===========================================================================
# Invalid sequences
# ===========================================================================


class TestSequencesInvalid:
    def test_non_empty_flow_sequence(self):
        # Only [] is allowed; [a, b] (flow sequence with content) is forbidden.
        fail("key: [a, b]\n")

    def test_compact_mapping_in_sequence_item(self):
        # "- key: val" is compact block mapping notation — not supported.
        fail("- key: val\n", "Compact mapping")

    def test_bare_dash_with_no_block(self):
        # A bare "-" at end of line with no indented block following is invalid.
        fail("-\n", "Bare empty sequence item")

    def test_non_empty_flow_sequence_root(self):
        fail("[a, b, c]\n")
