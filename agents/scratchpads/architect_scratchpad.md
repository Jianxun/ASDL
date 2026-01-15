# Architect Scratchpad

## AST->GraphIR pattern handling (atomized-only + provenance)

Current issues:
- `src/asdl/ir/converters/ast_to_graphir.py` preserves raw pattern expressions; it does **not** atomize patterns.
- IFIR atomization/elaboration passes are being removed; GraphIR must be atomized.
- GraphIR pattern bundle ops are being removed; provenance must live on ops.
- No module-level pattern expression table exists yet for diagnostics or rebundling.

Decisions (latest):
- GraphIR is atomized-only; it does not render patterns.
- Pattern provenance is attached to nets/instances/endpoints/params via typed
  `graphir.pattern_origin`.
- `pattern_origin` fields: `expression_id`, `segment_index` (0-based),
  `base_name`, `pattern_parts` (ordered substitutions).
- Pattern expression table lives in `graphir.module.attrs["pattern_expression_table"]`
  with entries `{expression, kind, span}` keyed by `expression_id`.
- Endpoint expressions expand as a single pattern expression (e.g., `MN<P|N>.<S|D>`),
  then each expanded atom is split on `.`; each atom must contain exactly one `.`.
- Instance name and instance param patterns expand together (zip by instance index;
  scalar broadcast allowed).
- Binding logic stays inside `ast_to_graphir.py` (no helper split yet).

Terminology (agreed):
- Pattern expression: full authored string (may include `;` and groups).
- Pattern segment: `;`-delimited piece of a pattern expression.
- Pattern atom: literal atom; endpoints may include a single `.`.
- Pattern parts: ordered substitution values per atom (operator occurrence order).

Next for AST->GraphIR (do not read full file yet):
- Introduce helper APIs under `src/asdl/ir/patterns/` for pattern_origin encoding,
  pattern expression table, pattern_parts, and endpoint atom splitting.
- Update AST->GraphIR lowering to:
  - register expression table entries
  - attach pattern_origin to atomized nets/instances/endpoints/params
  - expand endpoint expressions as a whole, then split on `.`.
  - maintain binding checks in `ast_to_graphir.py`.
