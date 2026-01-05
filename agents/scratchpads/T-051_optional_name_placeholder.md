# T-051 Optional {name} Placeholder

## Task summary
- DoD: Remove the requirement that backend device templates include `{name}`. Allow pure-instruction templates; keep `{ports}` optional. Update diagnostics/tests to match the new rule.
- Verify: `pytest tests/unit_tests/emit -v`, `pytest tests/unit_tests/netlist -v`

## Read
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/handoff.md`
- `config/backends.yaml`
- `src/asdl/emit/netlist/api.py`
- `src/asdl/emit/netlist/diagnostics.py`
- `src/asdl/emit/netlist/render.py`
- `src/asdl/emit/netlist/templates.py`
- `src/asdl/emit/netlist/verify.py`
- `tests/unit_tests/netlist/test_netlist_emitter.py`

## Plan
1. Remove `{name}` placeholder requirement for device templates in template validation.
2. Update netlist unit tests to cover instruction-only templates and drop missing-placeholder expectation.
3. Run emit/netlist tests.

## Progress log
- Created branch `feature/T-051-optional-name-placeholder`.
- Removed device template `{name}` requirement in template validation.
- Updated netlist unit test to allow instruction-only templates.
- Ran unit tests for emit and netlist suites.

## Patch summary
- `src/asdl/emit/netlist/templates.py`: allow device templates without required placeholders.
- `tests/unit_tests/netlist/test_netlist_emitter.py`: replace missing-placeholder test with instruction-template allowance.

## Verification
- `venv/bin/pytest tests/unit_tests/emit -v` (passed)
- `venv/bin/pytest tests/unit_tests/netlist -v` (passed)

## Status request
- Done

## Blockers / Questions
- None.

## Next steps
1. Commit changes and push branch.
2. Open PR referencing T-051 + scratchpad.
3. Request task status update to Done.
