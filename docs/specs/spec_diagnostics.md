# Spec — Diagnostics v0 (Shared Emission Contract)

## Purpose
Define a single diagnostic data contract used by all pipeline stages (parser, AST validation, IR conversion, passes, emission) so every surface (CLI, tests, future linter/LSP) consumes the same schema and location rules.

Diagnostics are the only user-facing error channel. Raw exceptions are reserved for internal bugs only.

---

## Conventions
- **Line/column are 1-based** for all spans and locations.
- `start` is **inclusive**, `end` is **exclusive**.
- A missing location should still emit a diagnostic (omit `primary_span` and include a note).
- Diagnostics must be **deterministically ordered** (see Ordering section).

---

## Core Types

### 1) `Severity`
Allowed values (v0):
- `info`
- `warning`
- `error`
- `fatal` (tool-level failure; should be rare)

### 2) `SourceSpan`
Represents a region in a source file.
- `file: str` (path or name)
- `start: { line: int, col: int }`
- `end: { line: int, col: int }`
- `byte_start: Optional[int]`
- `byte_end: Optional[int]`

### 3) `Label`
Secondary location with a short message.
- `span: SourceSpan`
- `message: Optional[str]`

### 4) `FixIt`
Represents a text edit.
- `span: SourceSpan`
- `replacement: str`
- `message: Optional[str]`

### 5) `Diagnostic`
Minimum required fields:
- `code: str` (stable identifier; see Codes section)
- `severity: Severity`
- `message: str`
- `primary_span: Optional[SourceSpan]`
- `labels: Optional[List[Label]]`
- `notes: Optional[List[str]]`
- `help: Optional[str]`
- `fixits: Optional[List[FixIt]]`
- `source: Optional[str]` (emitter, e.g. `parser`, `ast`, `ir`, `pass.select_view`)

---

## Codes
Codes must be stable across releases. Format (v0):
```
<DOMAIN>-<NNN>
```
Where `DOMAIN` is one of:
- `PARSE`, `AST`, `IR`, `PASS`, `EMIT`, `LINT`, `TOOL`

Example: `PARSE-001`, `AST-014`, `PASS-203`.

---

## Emission Rules
- **No user-facing exceptions**: emit diagnostics instead.
- A stage may emit multiple diagnostics; continue if possible.
- `fatal` indicates an unrecoverable tool failure but must still be reported via diagnostics.
- Diagnostics should prefer the **closest possible span** (node or field), not just file-level.

---

## Location Rules
- Parser must attach a `SourceSpan` to AST nodes using a `LocationIndex` built from YAML paths.
- AST to IR conversion must carry origin location into IR ops/attrs.
- IR passes must emit diagnostics using IR origin when available.
- If a span cannot be determined, emit the diagnostic with `primary_span` omitted and include a note.

---

## Ordering (Determinism)
Diagnostics are sorted before rendering:
1. `file` (lexicographic; missing file sorts last)
2. `start.line`, `start.col` (diagnostics without `primary_span` sort last)
3. `severity` (fatal > error > warning > info)
4. `code`
5. `message`

This order must be consistent across CLI and tests.

---

## Text Rendering (CLI)
Recommended format (v0):
```
<file>:<line>:<col>: <severity> <code>: <message>
  <label message> (line:col-line:col)
  note: <note>
  help: <help>
```
- Labels, notes, help, and fix-its are optional.
- If no span exists, display `<severity> <code>: <message>`.

---

## JSON Rendering
Top-level is a list of diagnostics with fields as defined above. Example:
```json
[
  {
    "code": "PARSE-001",
    "severity": "error",
    "message": "Unknown key: top_modee",
    "primary_span": {
      "file": "design.yaml",
      "start": { "line": 3, "col": 1 },
      "end": { "line": 3, "col": 9 }
    },
    "labels": [],
    "notes": ["Did you mean `top_mode`?"],
    "help": null,
    "fixits": [
      {
        "span": {
          "file": "design.yaml",
          "start": { "line": 3, "col": 1 },
          "end": { "line": 3, "col": 9 }
        },
        "replacement": "top_mode",
        "message": "Fix key spelling"
      }
    ],
    "source": "parser"
  }
]
```

---

## Non-Goals (v0)
- LSP diagnostic conversion details (future work).
- Rule configuration and lint suppression mechanism (future work).
- Auto-apply of fix-its (diagnostics only).
