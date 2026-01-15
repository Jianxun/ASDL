# T-131 Remove bundle usage from GraphIR converters

## Objective
- Remove bundle/pattern_expr handling in GraphIR->IFIR and GraphIR->AST converters.

## Notes
- Replace rebundling with pattern_origin + module table.

## Files
- src/asdl/ir/converters/graphir_to_ifir.py
- src/asdl/ir/converters/graphir_to_ast.py
- src/asdl/ir/patterns/origin.py
