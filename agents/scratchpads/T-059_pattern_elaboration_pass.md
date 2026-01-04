# T-059 Pattern Elaboration Pass

## Context
Patterns are preserved through AST/NFIR/IFIR; a dedicated elaboration pass expands them into explicit names before emission.

## Notes
- Expand names/endpoints using the shared expansion engine.
- Run before backend emission; keep emission unchanged.

## DoD
- Elaboration pass implemented and wired into pipeline.
- Tests verify explicit expansion + netlist output remains correct.
