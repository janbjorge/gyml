# gyml

YAML syntax, JSON semantics. No surprises.

---

## Why

Standard YAML is a minefield. The same file parsed by two different libraries
can produce different values. The Norway Problem (`NO` → `False`), implicit
type coercion, twelve ways to write null, anchors that turn config files into
programs — none of this belongs in a configuration format.

GYML fixes this by keeping only the parts of YAML that are unambiguous:

- **Block style only** — no flow mappings `{a: 1}` or flow sequences `[a, b]`
  (empty `{}` and `[]` are allowed as explicit empty-collection literals)
- **JSON scalar types** — `true`/`false`, `null`, integers, floats, strings.
  No `yes`/`no`, no `~`, no `.inf`, no `0xFF`
- **Double-quoted strings only** — single quotes are rejected
- **No anchors, aliases, or tags** — no `&ref`, `*ref`, `!!python/object`
- **Duplicate keys are a hard error**
- **Indentation is strict** — multiples of 2 spaces, tabs rejected

Valid GYML is always valid YAML. The reverse is not true, which is the point.

---

## Install

```bash
pip install gyml
# or
uv add gyml
```

---

## Usage

### Python API

```python
from gyml import loads, load

# Parse a string
config = loads("""
database:
  host: localhost
  port: 5432
  ssl: true
""")
# → {"database": {"host": "localhost", "port": 5432, "ssl": True}}

# Parse a file
config = load("config.gyml")
```

Two functions, that's it. Both return plain Python objects — `dict`, `list`,
`str`, `int`, `float`, `bool`, or `None`. No wrapper types, no schema needed.

### Error handling

```python
from gyml import loads, ParseError

try:
    loads("port: 0xFF")
except ParseError as e:
    print(e)  # line 1, col 7: "0xFF" — hex/octal/binary literals are not allowed
```

`ParseError` carries `message`, `line`, and `col` (both 1-based) so you can
point the user directly at the offending character.

### CLI

```bash
gyml config.gyml            # pretty-print as JSON to stdout
```

---

## What valid GYML looks like

```yaml
# Scalars
name: Alice
age: 30
score: 9.5
active: true
notes: null

# Quoted string (preserves reserved words as strings)
status: "true"
id: "404"

# Nested mapping
server:
  host: 0.0.0.0
  port: 8080

# Sequence
allowed_hosts:
  - localhost
  - 127.0.0.1

# Sequence of mappings
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
```

---

## What GYML rejects (and why)

| Input | Error | Reason |
|---|---|---|
| `key: ~` | not a valid null | use `null` |
| `key: Yes` | not a valid boolean | use `true` or `false` |
| `key: 0xFF` | hex/octal/binary not allowed | no implicit base conversion |
| `key: .inf` | .inf/.nan not allowed | not a JSON value |
| `key: 1_000` | underscore separators not allowed | ambiguous |
| `key: 'val'` | single-quoted strings not allowed | use double quotes |
| `true: val` | boolean literals not allowed as keys | use `"true"` |
| `a: 1\na: 2` | duplicate key | silent overwrites are bugs |
| `key:\n` | bare empty value | write `null` explicitly |

---

## Compared to alternatives

| | GYML | PyYAML | StrictYAML |
|---|---|---|---|
| Auto-typed scalars | yes | yes (dangerously) | no (strings by default) |
| Schema required | no | no | optional |
| Norway problem | impossible | present | impossible |
| Runtime dependencies | **zero** | yes | yes (ruamel) |
| From-scratch parser | yes | no | no |
