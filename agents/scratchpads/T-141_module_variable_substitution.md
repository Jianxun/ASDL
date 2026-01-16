# T-141 Module variable substitution in instance params

## Task summary (DoD + verify)
- Implement `{var}` substitution for module variables in instance parameter values during AST->GraphIR lowering.
- Allow variables to reference other variables, detect cycles/undefined variables with diagnostics, and apply substitution before parameter pattern expansion.
- Restrict substitution to instance parameter values only.
- Add unit tests for success, undefined variables, and recursion errors.
- Verify: `venv/bin/pytest tests/unit_tests/ir/test_graphir_converter.py -v`

## Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`

## Plan
- [ ] Add GraphIR converter tests for module variable substitution success + errors.
- [ ] Resolve module variable substitution in AST->GraphIR lowering with diagnostics.
- [ ] Verify with targeted pytest.

## Progress log
- Initialized scratchpad and read context.
- Added GraphIR converter tests for module variable substitution + error diagnostics.
- Implemented module variable substitution with recursion/undefined detection in lowering.
- Verified `tests/unit_tests/ir/test_graphir_converter.py`.

## Patch summary
- Added GraphIR converter coverage for module variable substitution success/undefined/recursion cases.
- Implemented module variable resolver and substitution before param pattern expansion.

## PR URL
- https://github.com/Jianxun/ASDL/pull/149

## Verification
- `venv/bin/pytest tests/unit_tests/ir/test_graphir_converter.py -v`

## Status request
- Ready for Review

## Blockers / Questions
- None.

## Next steps
- Implement substitution logic and diagnostics; add tests; run verify.
