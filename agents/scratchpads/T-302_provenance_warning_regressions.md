# T-302 — Add provenance warnings and deterministic compile-log regression coverage

## Task summary (DoD + verify)
- DoD:
  Emit warnings when module/file provenance metadata is missing or unknown
  (including non-end-to-end partial pipeline cases), keep `{file_id}`
  provenance behavior in subckt headers, and add deterministic regression
  coverage for emitted collision naming and compile-log ordering/contents.
  Remove obsolete assertions for hash-based names and sidecar-only outputs.
- Verify:
  `./venv/bin/pytest tests/unit_tests/netlist/test_netlist_render_netlist_ir.py tests/unit_tests/cli/test_netlist.py tests/unit_tests/views -k "collision or provenance or log or deterministic" -v`

## Read (paths)
- agents/roles/executor.md
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

## Plan
- Add provenance warning diagnostics in netlist rendering for missing/unknown metadata paths.
- Ensure emitted-name collision allocation remains deterministic for partial provenance inputs.
- Add deterministic regressions for netlist render + CLI compile log payload ordering/content.
- Run target verifies and record results.

## Milestone notes
- Intake complete; branch created (`feature/T-302-provenance-warning-regressions`) and task set to `in_progress`.
- Added explicit provenance warnings for missing/unknown `entry_file_id`, module `file_id`, and instance `ref_file_id` ambiguity/unknown cases.
- Hardened module emitted-name map keying to remain deterministic when partial-pipeline inputs contain duplicate `(file_id, symbol)` tuples.
- Added deterministic regressions for missing-provenance rendering and compile-log collision payload content/order.

## Patch summary
- `src/asdl/emit/netlist/diagnostics.py`
  - Added new warning code `EMIT-015` (`PROVENANCE_METADATA_WARNING`).
- `src/asdl/emit/netlist/render.py`
  - Added provenance warning emission path for:
    - missing design `entry_file_id` fallback behavior,
    - missing module `file_id` used in `__subckt_header__` `{file_id}` context,
    - missing/unknown instance `ref_file_id` provenance metadata.
  - Kept existing `{file_id}` rendering behavior, while making fallback explicit and warning-backed.
  - Changed internal emitted-name mapping keys to module identity (`id(module)`) so partial provenance inputs cannot overwrite deterministic mappings.
- `tests/unit_tests/netlist/test_netlist_render_netlist_ir.py`
  - Added regression proving:
    - provenance warnings are emitted for missing metadata,
    - deterministic collision naming still works with missing provenance,
    - `{file_id}` placeholder behavior in headers/calls is preserved.
- `tests/unit_tests/cli/test_netlist.py`
  - Added deterministic compile-log regression for collision cases asserting:
    - exact `emission_name_map` order/content,
    - warning/diagnostic counts and severity aggregates,
    - warning/diagnostic code entries for `EMIT-014`.

## PR URL
- Pending PR creation.

## Verification
- `./venv/bin/pytest tests/unit_tests/netlist/test_netlist_render_netlist_ir.py -k "provenance or collision_allocator or emission_name_map" -v`
  - Result: 3 passed, 5 deselected
- `./venv/bin/pytest tests/unit_tests/cli/test_netlist.py -k "log or collision or binding_sidecar" -v`
  - Result: 6 passed, 18 deselected
- `./venv/bin/pytest tests/unit_tests/netlist/test_netlist_render_netlist_ir.py tests/unit_tests/cli/test_netlist.py tests/unit_tests/views -k "collision or provenance or log or deterministic" -v`
  - Result: 11 passed, 42 deselected

## Status request (Done / Blocked / In Progress)
- Done

## Blockers / Questions
- None.

## Next steps
- Push branch, open PR to `main`, then set task state to `ready_for_review` with PR number.
