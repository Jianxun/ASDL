# T-130 Pattern metadata helper APIs

## Objective
- Add pattern metadata helper modules under `src/asdl/ir/patterns/`.

## Notes
- origin.py: PatternOrigin encode/decode for typed attr.
- expr_table.py: module attrs table helpers.
- parts.py: pattern_parts normalization + attr encode/decode.
- endpoint_split.py: split expanded endpoint atoms on `.`.

## Files
- src/asdl/ir/patterns/origin.py
- src/asdl/ir/patterns/expr_table.py
- src/asdl/ir/patterns/parts.py
- src/asdl/ir/patterns/endpoint_split.py
- src/asdl/ir/patterns/__init__.py
