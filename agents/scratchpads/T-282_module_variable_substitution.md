# T-282 — Implement module variable substitution with IR-012 and IR-013 diagnostics

## Task summary (DoD + verify)
- Implement `{var}` substitution for module variables in instance parameter values before parameter pattern expansion.
- Emit `IR-012` for undefined module variables in instance parameter substitutions.
- Emit `IR-013` for recursive module-variable substitutions.
- Include source spans in diagnostics where available.
- Verify:
  - `./venv/bin/pytest tests/unit_tests/lowering tests/unit_tests/netlist -v`

## Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `src/asdl/lowering/patterned_graph_to_atomized.py`
- `src/asdl/lowering/patterned_graph_to_atomized_context.py`
- `src/asdl/lowering/patterned_graph_to_atomized_instances.py`
- `tests/unit_tests/core/test_patterned_graph_atomize.py`
- `docs/specs/spec_diagnostic_codes.md`
- `agents/adr/ADR-0016-variables.md`

## Plan
1. Add/adjust atomization tests for module variable substitution and IR-012/IR-013 diagnostics (with span assertions).
2. Implement module-variable placeholder resolution in atomization context and apply substitution before parameter pattern expansion.
3. Run targeted tests, then full task verify command.
4. Close out scratchpad, update task state, and open PR.

## Milestone notes
- Intake complete; task state set to `in_progress`; branch `feature/T-282-module-variable-substitution` created.
- Added regression tests for substitution success, undefined-variable diagnostics (`IR-012`), and recursive-variable diagnostics (`IR-013`).
- Implemented module-variable substitution during atomization instance-param expansion, before parameter pattern expansion.

## Patch summary
- Added module-variable placeholder substitution in `src/asdl/lowering/patterned_graph_to_atomized_context.py`:
  - Introduced `IR-012`/`IR-013` diagnostic codes.
  - Added recursive placeholder resolution with cycle detection and caching.
  - Added span-aware diagnostics (parameter span preferred for `IR-012`, module span preferred for `IR-013`).
- Updated instance parameter expansion in `src/asdl/lowering/patterned_graph_to_atomized_instances.py`:
  - Substitutes module variables from `PatternExpr.raw` first.
  - Re-parses substituted parameter expression and then runs pattern expansion.
- Added regression coverage in `tests/unit_tests/core/test_patterned_graph_atomize.py`:
  - Substitution-before-expansion behavior.
  - Undefined variable diagnostic coverage.
  - Recursive variable diagnostic coverage.

## PR URL
- To be populated from PR creation output.

## Verification
- `./venv/bin/pytest tests/unit_tests/core/test_patterned_graph_atomize.py -k 'substitutes_module_variables or undefined_module_variable or recursive_module_variable' -v` (pass)
- `./venv/bin/pytest tests/unit_tests/core/test_patterned_graph_atomize.py -v` (pass)
- `./venv/bin/pytest tests/unit_tests/lowering tests/unit_tests/netlist -v` (pass)

## Status request
- In Progress

## Blockers / Questions
- None.

## Next steps
- Push branch, open PR, set task state to `ready_for_review` with PR number.
