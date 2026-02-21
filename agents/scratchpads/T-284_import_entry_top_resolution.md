# T-284: Fix imported-program top inference to respect entry-file module scope

## Task summary (DoD + verify)
- DoD:
  - Preserve entry-file identity through NetlistIR lowering when `top` is omitted.
  - Resolve implicit top only from modules defined in the entry file.
  - Keep deterministic error behavior when entry file has zero or multiple modules without explicit `top`.
  - Add regression coverage for import-driven entry builds with one local module and no explicit `top`.
- Verify:
  - `./venv/bin/pytest tests/unit_tests/lowering/test_atomized_graph_to_netlist_ir.py tests/unit_tests/netlist/test_netlist_render_netlist_ir.py tests/unit_tests/cli/test_netlist.py -v`

## Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `src/asdl/lowering/atomized_graph_to_netlist_ir.py`
- `src/asdl/lowering/__init__.py`
- `src/asdl/emit/netlist/ir_utils.py`
- `src/asdl/emit/netlist/render.py`
- `tests/unit_tests/lowering/test_atomized_graph_to_netlist_ir.py`
- `tests/unit_tests/netlist/test_netlist_render_netlist_ir.py`
- `tests/unit_tests/cli/test_netlist.py`

## Plan
1. Add regression tests that cover import-driven omitted-top scenarios.
2. Thread/preserve `entry_file_id` through NetlistIR lowering and implicit top inference.
3. Update render-time top selection to scope implicit inference to entry-file modules.
4. Run task verify command and close out state for review.

## Milestone notes
- Added failing tests for lowering, render, and CLI import flows with omitted `top`.
- Implemented entry-file-scoped implicit top inference in lowering + NetlistIR top resolution.
- Updated CLI fixture for zero-entry-module scenario to remain schema-valid while still testing `EMIT-001`.

## Patch summary
- Added `entry_file_id` input to `build_netlist_ir_design` and used it to infer implicit top from entry-file modules only.
- Preserved `entry_file_id` in pipeline lowering for both import-graph and document flows.
- Updated NetlistIR top resolution to:
  - infer implicit top from exactly one entry-file module when `top` is omitted;
  - emit deterministic `EMIT-001` when entry file has zero/multiple modules and no explicit top.
- Removed conflicting renderer precheck that assumed global single-module behavior.
- Added regression tests in lowering, netlist render, and CLI suites.

## PR URL
- Pending PR creation.

## Verification
- `./venv/bin/pytest tests/unit_tests/lowering/test_atomized_graph_to_netlist_ir.py tests/unit_tests/netlist/test_netlist_render_netlist_ir.py tests/unit_tests/cli/test_netlist.py -v` (pass, 16 passed)

## Status request
- In Progress

## Blockers / Questions
- None.

## Next steps
- Push branch and open PR against `main`.
- Update task state to `ready_for_review` with PR number.
