# Architect Scratchpad

## Pattern atomization into GraphIR (AST origin metadata)

Current implementation issues:
- `src/asdl/ir/converters/ast_to_graphir.py` preserves raw pattern expressions; it does **not** atomize patterns.
- GraphIR `graphir.bundle` / `graphir.pattern_expr` ops are defined but never emitted by AST->GraphIR.
- Atomization currently happens in IFIR (`PatternAtomizePass`), so GraphIR contains pattern delimiters and loses AST-origin metadata.
- `graphir_to_ifir._check_pattern_binding_lengths` relies on pattern expression metadata, so it is effectively bypassed today.
- `asdl.patterns.atomize` returns `expression`/`literal`/`origin` without `base_name` + `suffix_parts`, so AST->GraphIR lacks structured metadata for rebundling/diagnostics.
- No `pattern_expression_id` table exists in GraphIR/IFIR, so diagnostics cannot reference authored expressions or spans.

Spec-defined GraphIR bundles (not implemented in AST->GraphIR):
- `docs/specs/spec_asdl_graphir.md` defines `graphir.bundle` and `graphir.pattern_expr` with `pattern_expressions` + `pattern_eligible` annotations.
- These ops exist in `src/asdl/ir/graphir/ops_pattern.py` and `src/asdl/ir/graphir/patterns.py`, but AST->GraphIR does not emit them.

Decisions: terminology and metadata strategy for AST->GraphIR

Terminology (agreed):
- Pattern expression: full authored string (may include `;` and groups).
- Pattern segment: `;`-delimited piece of a pattern expression.
- Pattern atom: `(base_name, [suffix_parts])` where suffix_parts are per-atom values (e.g., `["p", 7]`).

Metadata strategy (agreed):
- Atomize in AST->GraphIR; GraphIR names are literal atoms and remain the identity.
- Attach structured metadata to each atom:
  - `pattern_expression_id`
  - `pattern_segment_index`
  - `base_name`
  - `suffix_parts` (typed `str`/`int`, possibly empty)
  - Optional group-boundary metadata when needed (enum vs range) for pairing/symmetry invariants.
- Maintain a module/design-level `pattern_expression_table`:
  - `pattern_expression_id -> (pattern_expression_string, pattern_expression_span)`
- Carry the metadata through IFIR; strip only during emission.
- Literal collisions are still detected by literal name identity (metadata does not change identity).

Refactor note:
- Use "pattern expression" in API naming; the term "token" is deprecated.

Open impacts:
- `graphir_to_ifir._check_pattern_binding_lengths` will need to be reconciled with atomized GraphIR + `pattern_expression_id` metadata.
- AST->GraphIR atomization needs richer metadata output from pattern helpers (base_name + suffix_parts).
