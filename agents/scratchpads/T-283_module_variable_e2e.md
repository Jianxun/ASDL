# T-283 - module variables end-to-end coverage

## Task summary
- DoD:
  - Add regression coverage proving module-variable substitution in emitted netlists.
  - Add executable diagnostics cases for `IR-012` and `IR-013`.
- Verify target:
  - `./venv/bin/pytest tests/unit_tests/e2e/test_pipeline_mvp.py tests/unit_tests/cli/test_netlist.py -v`

## Read
- `agents/roles/executor.md`
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `agents/scratchpads/T-283_module_variable_e2e.md`

## Plan
1. Inspect existing tests/examples for module-variable substitution and diagnostics.
2. Add/adjust e2e and CLI coverage for successful substitution output.
3. Add/adjust diagnostics manifest/cases for `IR-012` and `IR-013`.
4. Run required verify command and record results.
5. Prepare closeout notes and PR handoff.

## Milestone notes
- Intake complete; task moved to `in_progress`.
- Added e2e regression for module-variable substitution in emitted netlists.
- Added CLI regressions for IR-012/IR-013 diagnostics and substitution success.
- Added diagnostics fixture case directories for IR-012/IR-013 and marked manifest entries ready.

## Patch summary
- `tests/unit_tests/e2e/test_pipeline_mvp.py`
  - Added a module-variable substitution success regression for emitted netlist output.
  - Added an example-driven regression using `examples/libs/sw_matrix/swmatrix_Tgate/swmatrix_Tgate.asdl` to verify substituted MOS sizing values appear in emitted `lvs.klayout` netlist lines.
- `tests/unit_tests/cli/test_netlist.py`
  - Added CLI regression for successful module-variable substitution in generated output file.
  - Added CLI diagnostics regressions that assert `IR-012` for undefined module variables and `IR-013` for recursive module-variable definitions.
- `tests/e2e/diagnostics/manifest.yaml`
  - Marked `IR-012` and `IR-013` case entries as `ready`.
- `tests/e2e/diagnostics/IR-012_undefined_module_variable/*`
  - Added executable fixture (`case.asdl`, `README.md`, `expected.txt`).
- `tests/e2e/diagnostics/IR-013_recursive_module_variable/*`
  - Added executable fixture (`case.asdl`, `README.md`, `expected.txt`).

## PR URL
- Pending creation

## Verification
- `./venv/bin/pytest tests/unit_tests/e2e/test_pipeline_mvp.py tests/unit_tests/cli/test_netlist.py -v`
  - Result: `20 passed`

## Status request (Done / Blocked / In Progress)
- In Progress (opening PR and updating `tasks_state` next)

## Blockers / Questions
- None.

## Next steps
- Push branch and open PR to `main`.
- Update `agents/context/tasks_state.yaml` to `ready_for_review` with PR number.
