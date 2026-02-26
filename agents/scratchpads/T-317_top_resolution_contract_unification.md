# T-317 — Unify top-module resolution contract with shared policy helper

## Task summary (DoD + verify)
- DoD: Introduce a shared top-resolution helper under `src/asdl/core/` with explicit policy controls for permissive traversal callers vs strict emission callers, then migrate `asdl.core.hierarchy` and `asdl.emit.netlist.ir_utils` to consume it. Preserve existing emission diagnostics behavior (`EMIT-001` cases/messages) while removing duplicated top-resolution semantics between hierarchy and netlist emission. Add regression coverage proving strict/permissive parity on ambiguous/missing top scenarios. Start by auditing existing query/views/emission helpers for reusable top/symbol selection behavior, and document in the scratchpad which logic is reused vs newly isolated.
- Verify:
  - `./venv/bin/pytest tests/unit_tests/core/test_hierarchy.py tests/unit_tests/netlist/test_netlist_render_netlist_ir.py -v`

## Read (paths)
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `docs/specs/spec_netlist_emission.md`
- `agents/adr/ADR-0039-shared-top-resolution-policy.md`

## Plan
- [ ] Perform reuse audit for top/symbol resolution across query/views/emission.
- [ ] Implement shared core helper with explicit strict/permissive policy controls.
- [ ] Migrate hierarchy + emission callers and delete duplicated helpers.
- [ ] Add/update regressions for ambiguous/missing top behavior.
- [ ] Run verify command and summarize reuse vs isolation decisions.

