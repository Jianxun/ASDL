# T-303 — Emit reachable-only module set from final resolved top realization

## Task summary (DoD + verify)
- DoD:
  Change netlist emission traversal to root at the final resolved top realization after view binding and emit only modules reachable from that top via transitive instance references. Unreachable authored/original module definitions must not be emitted. Preserve deterministic traversal and output ordering for reachable modules. Include regression updates in netlist and CLI tests that prove unreachable module blocks are pruned and top-level instantiation targets the final resolved top realization.
- Verify:
  `./venv/bin/pytest tests/unit_tests/views/test_view_apply.py tests/unit_tests/netlist/test_netlist_render_netlist_ir.py tests/unit_tests/cli/test_netlist.py -k "reachable or view or top" -v`

## Read (paths)
- agents/roles/executor.md
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md
- agents/adr/ADR-0036-reachable-only-emission-for-final-view-top.md
- src/asdl/emit/netlist/render.py
- src/asdl/emit/netlist/ir_utils.py
- src/asdl/views/api.py
- src/asdl/cli/__init__.py
- tests/unit_tests/netlist/test_netlist_render_netlist_ir.py
- tests/unit_tests/cli/test_netlist.py
- tests/unit_tests/views/test_view_apply.py

## Plan
- Inspect current top resolution, module traversal, and emission-name behavior in netlist rendering.
- Implement deterministic reachable-module collection rooted at selected top module.
- Emit only reachable modules and scope provenance checks to reachable modules.
- Add regression coverage for unreachable module pruning in renderer and CLI view-profile flow.
- Run verify command and record outcomes.

## Milestone notes
- Intake complete; task set to in_progress and state lint passes.
- Implemented reachable-only traversal and switched module emission loop to reachable set.
- Added focused regressions in netlist renderer and CLI view fixture profile.

## Patch summary
- Updated `src/asdl/emit/netlist/render.py`:
  - Added `_collect_reachable_modules_ir(...)` to compute transitive module reachability from the resolved top module using deterministic lookup and ordering.
  - Emission loop now iterates reachable modules only.
  - Provenance diagnostics now only scan reachable modules/instances.
- Updated `tests/unit_tests/netlist/test_netlist_render_netlist_ir.py`:
  - Added `test_render_netlist_ir_emits_only_modules_reachable_from_top` to verify unreachable modules are pruned from emitted subckt blocks.
- Updated `tests/unit_tests/cli/test_netlist.py`:
  - Added `test_cli_netlist_view_fixture_emits_reachable_only_from_final_top` to verify view-resolved top flow emits only reachable realization blocks (e.g., `shift_row_behave` emitted, `shift_row` pruned).

## PR URL
- Pending.

## Verification
- `./venv/bin/pytest tests/unit_tests/views/test_view_apply.py tests/unit_tests/netlist/test_netlist_render_netlist_ir.py tests/unit_tests/cli/test_netlist.py -k "reachable or view or top" -v`
  - Result: 17 passed, 20 deselected.

## Status request (Done / Blocked / In Progress)
- In Progress

## Blockers / Questions
- None.

## Next steps
- Commit changes and open PR for review.
