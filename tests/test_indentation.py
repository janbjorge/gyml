"""
Tests for indentation rules.

GYAML requires indentation to be a strict multiple of 2 spaces.
Tabs are always forbidden.  Dedenting to a level that was never pushed
is an error.
"""

from __future__ import annotations

from .conftest import fail, ok, ok_eq

# ===========================================================================
# Valid indentation
# ===========================================================================


class TestIndentationValid:
    def test_two_space_indent(self):
        ok("a:\n  b: 1\n")

    def test_four_space_via_two_levels(self):
        # Two levels of two-space indent → four total, which is valid.
        ok("a:\n  b:\n    c: 1\n")

    def test_dedent_to_root(self):
        src = "a:\n  b: 1\nc: 2\n"
        ok_eq(src, {"a": {"b": 1}, "c": 2})

    def test_sequence_two_space_indent(self):
        ok("items:\n  - a\n  - b\n")


# ===========================================================================
# Invalid indentation
# ===========================================================================


class TestIndentationInvalid:
    def test_one_space_indent(self):
        fail("a:\n b: 1\n", "multiple of 2")

    def test_three_space_indent(self):
        fail("a:\n   b: 1\n", "multiple of 2")

    def test_tab_in_indent(self):
        fail("a:\n\tb: 1\n", "Tabs")

    def test_inconsistent_dedent(self):
        # Indent to level 4, then dedent to level 2 which was never pushed —
        # the parser cannot match this to any open block.
        fail("a:\n    b:\n      c: 1\n  d: 2\n", "Inconsistent dedent")
