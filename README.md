# gyml

> YAML syntax. JSON semantics. Zero drama.

---

## The problem

Picture this. You are three coffees deep, 11pm, production is on fire. You trace
the bug to a config file. The value is `NO`. Just a string, right? Except PyYAML
read it as `False`. Because `NO` is the ISO country code for Norway and some YAML
1.1 designer decided it should coerce to a boolean. Your country abbreviation just
took down prod.

This is not a contrived edge case. It has happened to real engineers at real
companies with real on-call rotations.

The YAML spec contains 211 grammar productions spread across ten chapters. It has
five scalar styles. It has five ways to write null (`null`, `Null`, `NULL`, `~`,
and the empty node). It has anchors that let you embed logic inside a data file.
It has tags that let you instantiate arbitrary Python objects from a config:
`!!python/object/apply:os.system` is valid PyYAML.

The format was designed to be human-friendly. Instead it became a footgun with a
hair trigger, a thick manual, and a community of people who have all been burned
by it at least once and now paste `yaml: risky business` into every `package.json`
they touch.

GYML is the fix. It takes YAML's clean block syntax, the indented key-value style
that actually is nice to write, and pairs it with JSON's strict, unambiguous
semantics. No surprises. No Norway. No 11pm incidents from a boolean that used to
be a country.

---

## What GYML is

A strict subset of YAML. Everything valid GYML is also valid YAML.
The reverse is absolutely not true, which is entirely the point.

The rules fit on a sticky note:

- **One way to write each type.** `true`/`false` for booleans. `null` for
  null. Decimal integers and floats. Double-quoted strings. Done.
- **Block style only.** No flow mappings `{a: 1}`, no flow sequences `[a, b]`.
  Empty `{}` and `[]` are fine as explicit empty literals.
- **No dark arts.** Anchors (`&`), aliases (`*`), and tags (`!!`) are rejected
  at the lexer. Your config file is not a program.
- **Duplicate keys are a hard error.** Silent overwrites have caused too many
  bugs in too many codebases.
- **Strict indentation.** Multiples of 2 spaces. Tabs rejected. No exceptions.

---

## Install

```bash
# pip
pip install gyml

# uv (recommended)
uv add gyml
```

---

## Usage

### Parse a string

```python
from gyml import loads

config = loads("""
server:
  host: 0.0.0.0
  port: 8080
  debug: false
  workers: 4
""")

print(config["server"]["port"])   # 8080  (int, not string)
print(config["server"]["debug"])  # False (bool, not string)
```

### Parse a file

```python
from gyml import load

config = load("config.gyml")
```

Both functions return plain Python objects: `dict`, `list`, `str`, `int`,
`float`, `bool`, or `None`. No wrapper types. No schema required. What you see
is what you get.

### Error handling

Errors are precise. When something is wrong you get the exact line, column, and
a message that tells you how to fix it, not a stack trace pointing at a C
extension.

```python
from gyml import loads, ParseError

try:
    loads("port: 0xFF")
except ParseError as e:
    print(e)
    # line 1, col 7: "0xFF" -- hex/octal/binary literals are not allowed
```

`ParseError` exposes three attributes:

| Attribute | Type | Description |
|---|---|---|
| `message` | `str` | Human-readable description of the violation |
| `line` | `int` | 1-based line number in the source |
| `col` | `int` | 1-based column number in the source |

### CLI

Convert any `.gyml` file to pretty-printed JSON:

```bash
gyml config.gyml                  # pretty-print to stdout
gyml config.gyml | jq '.server'   # pipe into jq
gyml config.gyml > out.json       # write to file
```

---

## What valid GYML looks like

```yaml
# All scalar types
name: Alice
age: 30
score: 9.5
active: true
notes: null

# Double-quoted strings preserve reserved words as strings
status: "true"
id: "404"

# Nested mapping
database:
  host: localhost
  port: 5432
  ssl: true
  name: mydb

# Sequence of scalars
allowed_hosts:
  - localhost
  - 127.0.0.1
  - 10.0.0.0

# Sequence of mappings (dash alone on its line, mapping indented below)
users:
  -
    name: Alice
    role: admin
  -
    name: Bob
    role: viewer

# Empty collection literals
cache: {}
tags: []

# Deeply nested is fine
services:
  web:
    image: nginx
    ports:
      - 80
      - 443
  db:
    image: postgres
    env:
      POSTGRES_DB: mydb
      POSTGRES_USER: admin
```

---

## What GYML rejects (and why)

Every one of these is valid YAML. Every one of them has caused a real bug in
someone's production system.

| Input | Error | Why it's banned |
|---|---|---|
| `country: NO` | not a valid boolean | Norway Problem; use `"NO"` |
| `enabled: yes` | not a valid boolean | use `true` |
| `level: on` | not a valid boolean | use `true` |
| `value: ~` | not a valid null | use `null` |
| `value: NULL` | not a valid null | use `null` |
| `port: 0xFF` | hex/octal/binary not allowed | no implicit base conversion |
| `ratio: .inf` | .inf/.nan not allowed | not a JSON value |
| `count: 1_000` | underscore separators not allowed | ambiguous in plain scalars |
| `key: 'val'` | single-quoted strings not allowed | one quoting style, double |
| `true: val` | boolean literals not allowed as keys | use `"true"` |
| `a: 1\na: 2` | duplicate key | silent overwrites are bugs |
| `key:\n` | bare empty value | write `null` explicitly |
| `data: &anchor val` | anchors not allowed | configs aren't programs |
| `ref: *anchor` | aliases not allowed | configs aren't programs |
| `obj: !!python/object` | tags not allowed | absolutely not |

---

## Compared to alternatives

| | GYML | PyYAML | StrictYAML |
|---|---|---|---|
| Auto-typed scalars | yes | yes (dangerously) | no (strings only by default) |
| Schema required | no | no | optional |
| Norway problem | impossible | present | impossible |
| `!!python/object` | rejected | allowed | rejected |
| Duplicate key detection | hard error | silent overwrite | hard error |
| Runtime dependencies | **zero** | yes | yes (ruamel) |
| From-scratch parser | yes | no | no |
| Spec size | sticky note | 211 grammar productions | medium |

---

## Get going

```bash
# clone
git clone https://github.com/janbjorge/gyml.git
cd gyml

# install deps (uv required)
uv sync

# run the tests
uv run pytest

# lint + format check
uv run ruff check gyml/ tests/
uv run ruff format --check gyml/ tests/

# type-check
uv run ty check gyml/
```

All four must pass clean before any change is considered done.

---

## Contributing

Contributions are welcome. A few ground rules:

- **No runtime dependencies.** The whole value proposition is zero deps.
  Don't add `ruamel`, `pyyaml`, or anything else.
- **No `Any`.** The codebase is fully typed. Keep it that way.
- **Tests for everything.** New behaviour gets a test. Bug fixes get a
  regression test. Use `ok()`, `ok_eq()`, and `fail()` from `conftest.py`.
- **Read `AGENTS.md`** before touching anything. It documents the architecture,
  naming conventions, and what the lexer vs. parser is responsible for.
- **Ruff and ty must be clean.** Run `uv run ruff check gyml/ tests/` and
  `uv run ty check gyml/` before opening a PR. CI will reject anything that
  isn't.

Open an issue first if you're planning something bigger than a bug fix. It's
worth a quick conversation before spending time on an approach that might not
fit the design.
