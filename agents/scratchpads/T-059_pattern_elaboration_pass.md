# T-059 Pattern Elaboration Pass

## Task summary
- DoD: Add an elaboration pass that expands pattern tokens into explicit names/endpoints before backend emission. Wire it into the pipeline before IFIR->emit; add tests covering expansion + netlist output stability.
- Verify: `pytest tests/unit_tests/ir -v`, `pytest tests/unit_tests/netlist -v`

## Read
- `agents/roles/executor.md`
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `src/asdl/patterns.py`
- `src/asdl/ir/converters/nfir_to_ifir.py`
- `src/asdl/ir/ifir/dialect.py`
- `src/asdl/ir/pipeline.py`
- `src/asdl/emit/netlist/api.py`
- `src/asdl/emit/netlist/render.py`
- `src/asdl/emit/netlist/verify.py`
- `docs/specs/spec_asdl_pattern_expansion.md`
- `tests/unit_tests/ir/test_ifir_converter.py`
- `tests/unit_tests/netlist/test_netlist_emitter.py`

## Plan
1. Implement IFIR pattern elaboration pass using `expand_pattern`/`expand_endpoint`.
2. Wire elaboration into `emit_netlist` before verify/render.
3. Add IR and netlist tests for expansion and output stability.

## Progress log
- Created `feature/T-059-pattern-elaboration` branch.
- Set task `T-059` to `in_progress`.
- Added pattern elaboration pass and wired into netlist emission.
- Added IR/netlist tests for pattern expansion.
- Ran unit tests for IR + netlist coverage.
- Opened PR: https://github.com/Jianxun/ASDL/pull/49

## Patch summary
- `src/asdl/ir/pattern_elaboration.py`: new elaboration pass + runner for pattern expansion.
- `src/asdl/emit/netlist/api.py`: run elaboration before netlist verification/render.
- `tests/unit_tests/ir/test_pattern_elaboration.py`: new IR expansion test.
- `tests/unit_tests/netlist/test_netlist_emitter.py`: netlist expansion test.
- `agents/context/tasks_state.yaml`: status set to `in_progress`.

## Verification
- `venv/bin/pytest tests/unit_tests/ir -v`
- `venv/bin/pytest tests/unit_tests/netlist -v`
- Results: all tests passed.

## Status request
- Ready for Review

## Blockers / Questions
- None.

## Next steps
1. Wait for Reviewer feedback.
