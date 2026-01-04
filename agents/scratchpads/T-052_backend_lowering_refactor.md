# T-052 Backend Lowering Refactor

## Context
Backend lowering still mixes verification with rendering/emission and includes defensive checks that are redundant with verification. This should be cleaned up for readability and maintainability.

## Notes
- Focus on separation of concerns between verification and rendering.
- Avoid behavior changes in netlist output or diagnostics semantics.
- Candidate files: `src/asdl/emit/netlist/verify.py`, `src/asdl/emit/netlist/render.py`, `src/asdl/emit/netlist/templates.py`.

## DoD
- Verification and rendering responsibilities are clearly separated.
- Redundant defensive checks removed from rendering paths.
- Netlist output and diagnostics behavior remain unchanged.
