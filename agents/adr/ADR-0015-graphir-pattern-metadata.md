# ADR-0015: Atomized GraphIR pattern metadata and helper APIs

Status: Accepted

## Context
GraphIR is the canonical semantic core and is constructed from atomized pattern
expansions. It does not render patterns itself, but it must preserve enough
provenance to support diagnostics and GraphIR->AST projection. The existing
`graphir.bundle`/`graphir.pattern_expr` ops are complex and entangle bundling
logic with GraphIR core. We also need to support mid-expression patterns such
as `MN<P|N>.<S|D>`, where the expression expands as a whole and is then split
on the endpoint delimiter.

## Decision
- GraphIR stores only atomized names. Pattern rendering is not a GraphIR
  responsibility.
- Remove pattern bundling ops from the GraphIR dialect: `graphir.bundle` and
  `graphir.pattern_expr` are deprecated and will be deleted in the refactor.
- Pattern provenance is attached directly to atom ops:
  - `graphir.net.pattern_origin`
  - `graphir.instance.pattern_origin`
  - `graphir.endpoint.pattern_origin`
  - instance parameters carry per-param `pattern_origin`.
- Introduce a typed attribute `graphir.pattern_origin` with fields:
  - `expression_id` (string, points into a module-level table)
  - `segment_index` (0-based segment position within the pattern expression)
  - `base_name` (string)
  - `pattern_parts` (ordered list of string or integer substitutions)
- Add a module attribute table at `graphir.module.attrs["pattern_expression_table"]`
  that maps `expression_id` to:
  - `expression` string
  - `kind` (net|inst|endpoint|param)
  - optional source span
- Endpoint expressions expand as a single pattern expression, then each expanded
  atom is split on `.` to recover instance and port names. Each atom must contain
  exactly one `.`.
- Helper APIs live under `src/asdl/ir/patterns/` and focus on metadata and table
  management, not binding:
  - `origin.py`: encode/decode `graphir.pattern_origin` typed attr.
  - `expr_table.py`: register/lookup entries in the module pattern table.
  - `parts.py`: normalize/encode/decode `pattern_parts`.
  - `endpoint_split.py`: split expanded endpoint atoms on `.` with validation.
  - Binding remains in `src/asdl/ir/converters/ast_to_graphir.py`.

## Consequences
- GraphIR ops gain typed `pattern_origin` attributes and module attrs gain a
  pattern expression table; the schema and verifiers must be updated.
- GraphIR->AST projection uses `pattern_origin` + expression table to rebundle
  deterministically without inferring patterns.
- Pattern metadata is uniform across nets, instances, endpoints, and params,
  simplifying diagnostics and lowering.

## Alternatives
- Keep `graphir.bundle`/`graphir.pattern_expr` and teach GraphIR to rebundle:
  rejected due to complexity and misplaced responsibilities.
- Store pattern provenance in untyped annotations:
  rejected because it weakens verification and type safety.
