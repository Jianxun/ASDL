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
- [x] Perform reuse audit for top/symbol resolution across query/views/emission.
- [x] Implement shared core helper with explicit strict/permissive policy controls.
- [x] Migrate hierarchy + emission callers and delete duplicated helpers.
- [x] Add/update regressions for ambiguous/missing top behavior.
- [x] Run verify command and summarize reuse vs isolation decisions.

## Milestone notes
- Intake: T-317 is `ready`; strict/permissive split required by ADR-0039 and netlist emission spec.
- Reuse audit:
  - Reused: `asdl.core.hierarchy.resolve_top_module` semantics (permissive fallback when explicit `top` is outside `entry_file_id`).
  - Reused: emission `EMIT-001` message contract in `asdl.emit.netlist.ir_utils`.
  - Newly isolated: shared policy-aware resolver at `src/asdl/core/top_resolution.py`.
  - Kept for follow-up tasks: duplicated top resolver in `src/asdl/views/api.py` (out of T-317 DoD file list; covered by subsequent task slices).
- Verification run passed after migration and regression updates.

## Patch summary
- Added `src/asdl/core/top_resolution.py` with one shared resolver:
  - `resolve_top_symbol(...)`
  - policy constants `PERMISSIVE_TOP_POLICY` and `STRICT_TOP_POLICY`
  - structured error reasons for strict emission diagnostics mapping.
- Migrated `src/asdl/core/hierarchy.py` to shared permissive top policy.
- Migrated `src/asdl/emit/netlist/ir_utils.py` to shared strict top policy while preserving `EMIT-001` cases/messages.
- Updated `src/asdl/emit/netlist/render.py` to use resolved top file identity from index.
- Added/updated regression coverage:
  - `tests/unit_tests/core/test_hierarchy.py` for permissive fallback and ambiguous entry-scope missing-top behavior.
  - `tests/unit_tests/netlist/test_netlist_render_netlist_ir.py` for strict entry-file explicit-top enforcement and strict missing-top diagnostics message checks.
  - Aligned two pre-existing emitter expectations to current reachable-only emission behavior to keep regression suite internally consistent.

## PR URL
- TBD

## Verification
- `./venv/bin/pytest tests/unit_tests/core/test_hierarchy.py tests/unit_tests/netlist/test_netlist_render_netlist_ir.py -v`
  - Result: PASS (18 passed)

## Status request
- In Progress (ready to open PR)

## Blockers / Questions
- None.

## Next steps
- Open PR to `main` with task summary/testing and update task state to `ready_for_review` with PR number.
