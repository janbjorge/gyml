"""
Tests for document-level rules.

Covers the root value of a document (scalar, mapping, sequence, empty),
comment handling, trailing-newline tolerance, and constructs that GYAML
explicitly forbids (anchors, aliases, tags, document separators).
"""

from __future__ import annotations

from .conftest import fail, ok_eq

# ===========================================================================
# Valid documents
# ===========================================================================


class TestDocumentValid:
    def test_empty_file(self):
        ok_eq("", None)

    def test_blank_lines_only(self):
        ok_eq("\n\n\n", None)

    def test_comment_only(self):
        ok_eq("# just a comment\n", None)

    def test_root_mapping(self):
        ok_eq("a: 1\n", {"a": 1})

    def test_root_sequence(self):
        ok_eq("- 1\n- 2\n", [1, 2])

    def test_root_plain_string(self):
        ok_eq("hello\n", "hello")

    def test_root_integer(self):
        ok_eq("42\n", 42)

    def test_root_float(self):
        ok_eq("3.14\n", 3.14)

    def test_root_bool(self):
        ok_eq("true\n", True)

    def test_root_null(self):
        ok_eq("null\n", None)

    def test_root_empty_mapping(self):
        ok_eq("{}\n", {})

    def test_root_empty_sequence(self):
        ok_eq("[]\n", [])

    def test_inline_comment_stripped(self):
        ok_eq("key: val # this is a comment\n", {"key": "val"})

    def test_comment_between_keys(self):
        ok_eq("a: 1\n# comment\nb: 2\n", {"a": 1, "b": 2})

    def test_trailing_newline(self):
        ok_eq("key: val\n", {"key": "val"})

    def test_no_trailing_newline(self):
        # Parsers must tolerate documents without a final newline.
        ok_eq("key: val", {"key": "val"})

    def test_blank_line_between_root_keys(self):
        # Blank lines between top-level mapping keys fold into one mapping.
        ok_eq("a: 1\n\nb: 2\n", {"a": 1, "b": 2})


# ===========================================================================
# Invalid documents
# ===========================================================================


class TestDocumentInvalid:
    def test_document_separator_rejected(self):
        # "---" is a YAML document separator; GYAML does not support it.
        fail("---\nkey: val\n")

    def test_anchor_rejected(self):
        fail("key: &anchor val\n")

    def test_alias_rejected(self):
        fail("key: *alias\n")

    def test_tag_rejected(self):
        fail("key: !!str val\n")

    def test_two_root_scalars_rejected(self):
        # A document can have only one root value.
        fail("hello\nworld\n", "Unexpected token")
