# T-304 Preserve canonical realized naming under reachable-only emission

## Task summary (DoD + verify)
- DoD: Keep emitted name policy consistent with ADR-0036 while enforcing
  uniqueness only within the reachable module set: default/undecorated and
  `cell@default` emit as `cell`; non-default emits as `cell_<view>`;
  collisions allocate deterministic ordinal suffixes (`__2`, `__3`, ...).
  Ensure mixed-view realized variants remain deterministic and readable
  without reintroducing occurrence-specialized naming. Include regression
  updates in CLI/view/netlist tests for `emission_name_map`, warning
  counts/messages, and deterministic naming under reachable-only emission.
- Verify:
  - `./venv/bin/pytest tests/unit_tests/netlist/test_netlist_render_netlist_ir.py tests/unit_tests/netlist/test_netlist_emitter.py tests/unit_tests/views/test_view_resolver.py tests/unit_tests/cli/test_netlist.py -k "view or collision or default or deterministic or emission_name_map or warning" -v`

## Read (paths)
- agents/roles/executor.md
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

## Plan
- Inspect current reachable-only naming behavior and regression expectations.
- Add/adjust tests first where practical, then implement naming fixes.
- Run task verify command and capture results.
- Prepare closeout updates, PR, and task status transition.

## Milestone notes
- Intake complete; implementation pending.
- Added regression coverage for reachable-only collision allocation in render, emitter, and CLI compile log payloads.
- Updated renderer naming allocation and `build_emission_name_map` scoping to use reachable modules from the final resolved top realization.
- Ran task verify command; all selected tests pass.

## Patch summary
- `src/asdl/emit/netlist/render.py`
  - Name collision allocation now scopes to reachable modules during emission.
  - `build_emission_name_map` now scopes to reachable modules by resolving the effective top and collecting reachable modules using the same traversal rules as emission.
- `tests/unit_tests/netlist/test_netlist_render_netlist_ir.py`
  - Existing name-map regression now explicitly keeps tested modules reachable.
  - Added regressions to prove unreachable colliders are excluded from naming/suffix allocation and name-map output.
  - Updated preexisting-suffix collision expectation to reachable-only behavior.
- `tests/unit_tests/netlist/test_netlist_emitter.py`
  - Added regression for reachable-only naming that ignores unreachable colliders.
  - Updated warning expectation in default-top emitter test to include deterministic provenance warning + unknown-parameter warning.
- `tests/unit_tests/cli/test_netlist.py`
  - Added unreachable-collider compile-log fixture + regression asserting reachable-only `emission_name_map` and warning count.
  - Updated divergent view test to assert no unreachable-driven `stage__3` suffix.

## PR URL
- Pending.

## Verification
- `./venv/bin/pytest tests/unit_tests/netlist/test_netlist_render_netlist_ir.py tests/unit_tests/netlist/test_netlist_emitter.py tests/unit_tests/views/test_view_resolver.py tests/unit_tests/cli/test_netlist.py -k "view or collision or default or deterministic or emission_name_map or warning" -v`
  - Result: 29 passed, 41 deselected.

## Status request (Done / Blocked / In Progress)
- In Progress

## Blockers / Questions
- None.

## Next steps
- Implement and validate T-304 scope.
