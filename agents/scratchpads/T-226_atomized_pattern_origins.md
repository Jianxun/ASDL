# T-226 AtomizedGraph per-atom pattern origins

## Task summary (DoD + verify)
- DoD: Add an AtomizedPatternOrigin (or equivalent) dataclass in `src/asdl/core/atomized_graph.py` with explicit {expression_id, segment_index, atom_index, base_name, pattern_parts}. Add optional `pattern_origin` fields to AtomizedNet/AtomizedInstance/AtomizedEndpoint. Populate these fields during atomization by expanding patterns with a helper that returns atoms + parts (reuse/relocate logic from `_expand_pattern_atoms` in `atomized_graph_to_netlist_ir.py`). Ensure atomized origins are attached per literal atom (not per patterned id). Update `src/asdl/core/dump.py` to include atomized pattern origins in dumps.
- Verify: `venv/bin/pytest tests/unit_tests/netlist -v`

## Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`

## Plan
- Todo:
  - Inspect AtomizedGraph models and current pattern atomization paths.
  - Introduce AtomizedPatternOrigin and wire optional fields on atomized entities.
  - Add pattern expansion helper that yields atoms + parts; use it in atomization passes.
  - Update dumps to include atomized pattern origins.
  - Add/update tests and run verify.

## Progress log
- 2026-01-25 20:52 — Task intake; read context files; next step set task in_progress and create branch.
- 2026-01-25 20:53 — Set T-226 in_progress, ran lint_tasks_state, created feature branch; files: agents/context/tasks_state.yaml; next step implement atomized origins.
- 2026-01-25 20:54 — Added AtomizedPatternOrigin, atomization origin expansion, atomized graph dump helpers, and origin coverage test; files: src/asdl/core/atomized_graph.py, src/asdl/lowering/patterned_graph_to_atomized_patterns.py, src/asdl/lowering/patterned_graph_to_atomized_instances.py, src/asdl/lowering/patterned_graph_to_atomized_nets.py, src/asdl/core/dump.py, src/asdl/core/__init__.py, tests/unit_tests/core/test_patterned_graph_atomize.py.
- 2026-01-25 20:54 — Commit 0f8ce35 "Add atomized pattern origins to atomization".
- 2026-01-25 20:55 — Verified netlist unit tests: `venv/bin/pytest tests/unit_tests/netlist -v` (pass).
- 2026-01-25 20:57 — Opened PR https://github.com/Jianxun/ASDL/pull/236.
- 2026-01-25 20:57 — Set T-226 ready_for_review, updated tasks_state, ran lint_tasks_state; files: agents/context/tasks_state.yaml.
- 2026-01-26 00:02 — Reviewer intake; set T-226 review_in_progress; next step review diff, scope, and verification logs.
- 2026-01-26 00:03 — Confirmed PR targets main; no CI checks reported; relying on logged pytest run from scratchpad; next step scope/code review.
- 2026-01-26 00:04 — Scope review vs DoD complete; code review complete with no blockers; next step post review comment and proceed to merge/closeout.
- 2026-01-26 00:05 — Posted PR review comment; set T-226 review_clean; next step merge and closeout.
- 2026-01-26 00:06 — Set T-226 done/merged true for closeout; ran lint_tasks_state; next step commit/push and merge PR.

## Patch summary
- Added AtomizedPatternOrigin and pattern_origin fields on AtomizedNet/Instance/Endpoint.
- Expanded atomization to attach per-atom origins (nets, instances, endpoints) and added origin-aware expansion helper.
- Added AtomizedGraph dump helpers to include pattern origins.
- Added core test coverage for atomized pattern origin attachment.

## PR URL
- https://github.com/Jianxun/ASDL/pull/236

## Verification
- `venv/bin/pytest tests/unit_tests/netlist -v`

## Status request
- Ready for Review.

## Blockers / Questions
- None.

## Next steps
- Await reviewer feedback.
