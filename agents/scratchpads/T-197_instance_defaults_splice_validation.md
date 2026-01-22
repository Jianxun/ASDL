# T-197 Validate instance_defaults net tokens against splice rules

## Task summary (DoD + verify)
- DoD: Validate net tokens referenced by `instance_defaults` with the same pattern parsing and no-splice rules as `nets` entries. Emit IR-003 diagnostics for invalid/spliced default net tokens and only append `$` ports when validation succeeds. Add unit tests for spliced `$` defaults.
- Verify: `venv/bin/pytest tests/unit_tests/core/test_patterned_graph_lowering.py -v`

## Read
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`

## Plan
- [ ] Inspect instance_defaults handling in lowering.
- [ ] Add validation for default net tokens and enforce no-splice rule.
- [ ] Extend tests for spliced defaults and diagnostic expectations.
- [ ] Run verify command and record results.

## Progress log
- 2026-01-XX: Initialized scratchpad.

## Patch summary
- TBD.

## PR URL
- TBD.

## Verification
- Not run.

## Status request
- Not started.

## Blockers / Questions
- None yet.

## Next steps
- Review instance_defaults port-order logic and net token validation.
