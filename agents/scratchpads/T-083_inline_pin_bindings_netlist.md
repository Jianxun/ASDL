# T-083 Inline pin bindings netlist coverage

## Task summary (DoD + verify)
- DoD: netlist/e2e tests cover inline pin bindings for internal nets without listing endpoints in `nets`.
- DoD: netlist/e2e tests cover `$` inline bindings creating ports and affecting emitted port order.
- Verify: `pytest tests/unit_tests/netlist/test_netlist_emitter.py -v`

## Read
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `tests/unit_tests/e2e/test_pipeline_mvp.py`
- `tests/unit_tests/ir/test_converter.py`
- `src/asdl/ir/converters/ast_to_nfir.py`

## Plan
- [ ] Add e2e test for inline bindings with internal nets only (no `nets` block).
- [ ] Add e2e test for `$` inline bindings creating ports and port order.
- [ ] Run tests and capture verification output.

## Progress log
- 2026-01-09: Initialized task, set status to in_progress, created feature branch.
- 2026-01-09: Added e2e coverage for inline bindings with internal nets.
- 2026-01-09: Added e2e coverage for inline `$` bindings and port order.

## Patch summary
- Added e2e pipeline tests to validate inline pin bindings for internal nets and
  `$`-prefixed port creation/order.

## PR URL
- https://github.com/Jianxun/ASDL/pull/87

## Verification
- `./venv/bin/pytest tests/unit_tests/e2e/test_pipeline_mvp.py -k inline_bindings_internal -v`
- `./venv/bin/pytest tests/unit_tests/e2e/test_pipeline_mvp.py -k inline_bindings_port_order -v`
- `./venv/bin/pytest tests/unit_tests/netlist/test_netlist_emitter.py -v`
- `./venv/bin/pytest tests/unit_tests/e2e/test_pipeline_mvp.py -v`

## Status request
- Done.

## Blockers / Questions
- None.

## Next steps
- Open PR, update task status to ready_for_review.
