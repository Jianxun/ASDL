# Spec — Diagnostic Codes v0

## Purpose
This document enumerates every diagnostic code emitted by the ASDL toolchain.
It complements `docs/specs/spec_diagnostics.md` by mapping stable codes to their
meaning, source, and span expectations.

## Conventions
- Codes are stable identifiers in the form `<DOMAIN>-<NNN>`.
- Each entry lists severity, source, and trigger.
- `primary_span` is required when a diagnostic can be tied to a concrete source
  location; otherwise omit it and include the standard no-span note.

## Code Catalog

### PARSE (source: `parser`)
- `PARSE-001` (error): YAML parse error. Span: YAML mark when available.
- `PARSE-002` (error): document root is not a mapping. Span: 1:1 of the file.
- `PARSE-003` (error): AST validation error (type/shape/invariant). Span: best
  match from the location index; may be missing for synthetic paths.
- `PARSE-004` (error): file not found or unreadable. Span: none (edge case).

### AST (sources: `parser`, `imports`, `ast`)
- `AST-010` (error, source=`imports`): import path not found. Span: import value
  if available; may be missing when resolution fails before location binding.
- `AST-011` (error, source=`parser` or `imports`):
  - Parser: invalid import namespace or non-string import path.
  - Imports: malformed import path.
  Span: import key/value when available.
- `AST-012` (error, source=`imports`): import cycle detected. Span: import entry
  when available; may be missing when only a graph is present.
- `AST-013` (error, source=`parser`): duplicate namespace key in `imports`.
  Span: duplicate key.
- `AST-014` (error, source=`imports`): duplicate symbol name within a file.
  Span: symbol definition when available.
- `AST-015` (error, source=`imports`): ambiguous import path with multiple
  matches. Span: import entry when available.
- `AST-020` (error, source=`ast`): invalid named pattern (bad name, substitution
  collision, or invalid substitution target). Span: pattern name or owning node.
- `AST-021` (error, source=`ast`): undefined named pattern reference. Span:
  reference location when available.
- `AST-022` (error, source=`ast`): named pattern recursively references another
  named pattern. Span: pattern value or owning node.

### IR (source: `ir`)
- `IR-001` (error): invalid instance expression or missing reference. Span:
  instance name or module location.
- `IR-002` (error): invalid endpoint expression or endpoint references unknown
  instance. Span: net/endpoint location.
- `IR-003` (error): pattern length mismatch between instance/net expansion and
  parameter/endpoint expansion. Span: instance/net location.
- `IR-004` (error): pattern expansion collision on instance/net literals. Span:
  instance/net location.
- `IR-010` (error): unresolved qualified symbol `ns.symbol` or ambiguous
  qualified reference. Span: instance reference.
- `IR-011` (error): unresolved unqualified symbol or ambiguous reference. Span:
  instance reference.
- `IR-012` (error): undefined module variable in instance parameter. Span:
  parameter or module location.
- `IR-013` (error): recursive module variable substitution. Span: module
  location.
- `IR-020` (error): invalid GraphIR program (unexpected op types). Span: none
  (GraphIR may not retain origin).
- `IR-021` (error): invalid GraphIR module (unexpected op types). Span: none.
- `IR-022` (error): invalid GraphIR device (unexpected op types). Span: none.
- `IR-023` (error): unknown GraphIR reference (entry module missing). Span: none.
- `IR-024` (error): endpoint references unknown instance in GraphIR. Span: none.
- `IR-025` (error): invalid GraphIR pattern origin or missing pattern table.
  Span: none.
- `IR-030` (error, source=`core`): duplicate net name in AtomizedGraph module.
  Span: none.
- `IR-031` (error, source=`core`): duplicate instance name in AtomizedGraph
  module. Span: none.
- `IR-032` (error, source=`core`): AtomizedGraph endpoint references unknown
  net or instance. Span: none.
- `IR-033` (error, source=`core`): AtomizedGraph endpoint uses an undefined port
  for the referenced module or device. Span: none.
- `IR-050` (error, source=`emit`): NetlistIR name is not a literal (contains
  pattern delimiters, leading `$` on nets, or empty). Span: none.
- `IR-051` (error, source=`emit`): duplicate NetlistIR net name in module. Span:
  none.
- `IR-052` (error, source=`emit`): duplicate NetlistIR instance name in module.
  Span: none.
- `IR-053` (error, source=`emit`): NetlistIR connection targets an unknown net
  or duplicates a port binding. Span: none.
- `IR-054` (error, source=`emit`): NetlistIR module ports list has duplicates
  or references missing nets. Span: none.
- `IR-055` (error, source=`emit`): NetlistIR pattern_origin metadata references
  a missing pattern expression entry or mismatched kind. Span: none.

### LINT (source: `ir`)
- `LINT-002` (warning): default binding overridden by explicit net binding.
  Span: explicit net binding when available.

### PASS (sources: `pass`, `pattern`)
- `PASS-001` (error, source=`pass`): GraphIR verification failed. Span: none.
- `PASS-002` (error, source=`pass`): GraphIR program op missing. Span: none.
- `PASS-003` (error, source=`pass`): IFIR verification failed. Span: none.
- `PASS-004` (error, source=`pass`): IFIR design op missing. Span: none.
- `PASS-101` (error, source=`pattern`): invalid numeric range in pattern
  expression. Span: none (pattern origin not attached).
- `PASS-102` (error, source=`pattern`): empty enum in pattern expression. Span:
  none.
- `PASS-103` (error, source=`pattern`): empty splice segment in pattern
  expression. Span: none.
- `PASS-104` (error, source=`pattern`): duplicate atoms in pattern expansion.
  Span: none.
- `PASS-105` (error, source=`pattern`): pattern expansion exceeds size limit.
  Span: none.
- `PASS-106` (error, source=`pattern`): pattern expression cannot be tokenized
  or expanded (empty or invalid syntax). Span: none.
- `PASS-999` (error, source=`pass`): pipeline crash or invalid pipeline
  invocation. Span: none (tool-level failure).

### EMIT (source: `emit`)
- `EMIT-001` (error): top module is missing or cannot be resolved for emission.
  Span: top selection when available.
- `EMIT-002` (warning): instance overrides unknown parameter key. Span: instance
  location when available.
- `EMIT-003` (error): unknown symbol or placeholder reference during emission
  (missing device/module or unknown template placeholder). Span: reference
  location when available.
- `EMIT-004` (error): backend missing or cannot be loaded, or required system
  devices missing. Span: backend/device location when available.
- `EMIT-005` (error): required connection missing for instance port. Span:
  instance connection when available.
- `EMIT-006` (error): connection refers to unknown port. Span: connection when
  available.
- `EMIT-007` (error): required template placeholder missing in system device.
  Span: none (system template).
- `EMIT-008` (error): malformed template string (format parsing error). Span:
  template location when available.
- `EMIT-009` (error): IFIR design missing during netlist verification. Span:
  none.
- `EMIT-010` (error): netlist verification crash. Span: none (tool-level).
- `EMIT-011` (error): unresolved environment variable in template expansion.
  Span: template location when available.
- `EMIT-012` (error): instance overrides variable key. Span: instance location
  when available.
- `EMIT-013` (error): variable key collides with parameter or backend prop key.
  Span: device/backend location when available.

### TOOL (source: `cli`)
- `TOOL-001` (error): CLI failed to import a dependency for a subcommand. Span:
  none.
- `TOOL-002` (error): CLI failed to write output. Span: none.
- `TOOL-003` (error): CLI schema generation failed. Span: none.
