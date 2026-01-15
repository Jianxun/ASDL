# T-127 Remove GraphIR pattern ops

## Objective
- Remove GraphIR pattern ops (`graphir.bundle`, `graphir.pattern_expr`) and related helpers.

## Notes
- Drop pattern op exports and verification paths.
- Keep GraphIR atomized-only.

## Files
- src/asdl/ir/graphir/ops_pattern.py
- src/asdl/ir/graphir/patterns.py
- src/asdl/ir/graphir/dialect.py
- src/asdl/ir/graphir/ops_module.py
- src/asdl/ir/graphir/__init__.py
