# AGENTS.md — contributor guide for agentic coding tools

This file is read by automated coding agents (Claude Code, Copilot, etc.).
Follow every rule here precisely; do not invent conventions not listed.

---

## Project overview

GYAML is a strict YAML subset with JSON semantics — zero external runtime
dependencies, from-scratch parser, fully typed (no `Any`).

```
gyaml/
  __init__.py   # public API: loads(), load(), _cli()
  errors.py     # ParseError dataclass
  tokens.py     # TokenType, ScalarStyle, Token
  values.py     # GValue union, coerce_scalar()
  lexer.py      # Lexer  — source text → list[Token]
  parser.py     # Parser — list[Token] → GValue
tests/
  conftest.py   # ok(), ok_eq(), fail() helpers (auto-imported by pytest)
  test_scalars.py
  test_keys.py
  test_mappings.py
  test_sequences.py
  test_indentation.py
  test_document.py
  test_integration.py
```

---

## Build / environment

The project uses **uv** exclusively. Never use raw `pip` or `python setup.py`.

```bash
uv sync                  # create/update .venv and install all deps
uv run <cmd>             # run any command inside the managed venv
```

---

## Test commands

```bash
# Full suite
uv run pytest

# Single file
uv run pytest tests/test_scalars.py

# Single test by node id
uv run pytest tests/test_scalars.py::TestNumbersValid::test_float

# Single test by keyword (fuzzy match on name)
uv run pytest -k test_float

# Stop on first failure, show locals
uv run pytest -x -l

# Verbose output
uv run pytest -v
```

---

## Lint / type-check commands

```bash
# Lint + auto-fix
uv run ruff check --fix gyaml/ tests/

# Format
uv run ruff format gyaml/ tests/

# Type-check (ty, not pyright)
ty check gyaml/
```

All three must pass clean before any change is considered done.

---

## Code style

### General
- Line length: **88 characters** (ruff default).
- All files start with `from __future__ import annotations`.
- No `Any` — ever. If the type is truly unknown, model it explicitly with a
  Union or narrow with `assert`/`isinstance`.
- Prefer `Final` for module-level constants (`from typing import Final`).

### Imports
Order (enforced by ruff/isort):
1. `__future__`
2. stdlib
3. first-party (`gyaml.*`)

No third-party runtime imports — the package has zero runtime dependencies.
Test files may import `pytest`; conftest helpers are available via relative
import (`from .conftest import ok, ok_eq, fail`).

### Naming
| Kind | Convention | Example |
|---|---|---|
| Module-level constant | `_UPPER_SNAKE` with leading `_` | `_LOOSE_BOOLS` |
| Public constant / exported name | `UPPER_SNAKE` | `GValue` (type alias) |
| Private attribute / method | `_lower_snake` | `self._tokens` |
| Public method / function | `lower_snake` | `coerce_scalar()` |
| Class | `PascalCase` | `Lexer`, `ParseError` |
| Enum member | `UPPER_SNAKE` | `TokenType.SCALAR` |

### Typing
- Use `X | Y` syntax only in type comments / annotations where
  `from __future__ import annotations` is active.
- `GValue` is the recursive Union for all parsed values; use it as the return
  type for anything that produces a parsed value.
- Dataclasses use `@dataclass(frozen=True)` for immutable tokens;
  `@dataclass` (mutable) for `ParseError`.
- Enums inherit from `Enum` with `auto()` values — no explicit integers.
- Annotate every public function, method parameter, and return type.
  Private methods must also be annotated; no bare `def`.

### Docstrings
- Every public function, method, and class gets a docstring.
- Private methods get a one-line docstring explaining *why*, not *what*.
- Module docstrings describe responsibilities and list key names/types.
- Use plain prose — no numpy/google/sphinx style annotations inside
  docstrings; parameter docs go in the docstring body as plain text when
  non-obvious.

### Comments
- Comments explain *why* a decision was made, not *what* the code does.
- Section dividers use the established style:
  ```python
  # ------------------------------------------------------------------
  # Section name
  # ------------------------------------------------------------------
  ```
- Inline comments on enum/constant declarations are encouraged for
  non-obvious values.

---

## Error handling

- The only exception type in the public API is `ParseError` (a dataclass
  with `message: str`, `line: int`, `col: int`).
- Raise `ParseError` at the earliest point of detection — lexer for
  character-level violations, parser for structural violations.
- Never catch and re-raise as a generic `Exception`.
- `line` and `col` are always 1-based.
- Error messages must contain enough context for a human to fix the input
  (e.g. include the offending token text and a hint about the correct form).
- The `__str__` of `ParseError` formats as `"line L, col C: <message>"`.

---

## Architecture rules

- **Lexer** (`lexer.py`): text → `list[Token]`. Validates character-level
  rules (tab indentation, bad escapes, forbidden spellings). Does NOT coerce
  values — that is the parser's job.
- **Parser** (`parser.py`): `list[Token]` → `GValue`. Validates structural
  rules (duplicate keys, bare empty values, forbidden key types). Does NOT
  read source characters.
- **No ports/adapters, no protocols for I/O** — the only "I/O" is reading a
  string; adding abstraction layers here is over-engineering.
- Public API surface is exactly two functions: `loads(text)` and
  `load(path)`, both returning `GValue`. Do not expand this without strong
  justification.

---

## Adding tests

- New tests go in the appropriate `tests/test_<topic>.py` file.
- Use `ok(src)`, `ok_eq(src, expected)`, and `fail(src, *frags)` from
  `conftest` — never call `loads()` directly in tests except when you need
  to inspect the return value in detail.
- Group tests in classes: `TestXxxValid` for positive cases,
  `TestXxxInvalid` for cases that must raise `ParseError`.
- Test method names describe the specific input shape, not the expected
  outcome: `test_leading_zeros`, not `test_leading_zeros_raises_error`.
- `fail(src, *frags)` accepts fragment strings that must all appear in the
  error message — pin the fragment to the *rule* violated, not the full
  wording, so tests survive minor message rewording.

---

## What NOT to do

- Do not add runtime dependencies.
- Do not use `ruamel`, `pyyaml`, or any external YAML library anywhere.
- Do not use `Any` in type annotations.
- Do not write single-quoted YAML strings in test inputs (they are
  explicitly forbidden by the spec and will raise `ParseError`).
- Do not introduce flow-style mappings or sequences with content
  (only `{}` and `[]` are legal inline forms).
- Do not use `pyright` — the type checker is `ty`.
- Do not commit a `uv.lock` change without running `uv sync` first.
