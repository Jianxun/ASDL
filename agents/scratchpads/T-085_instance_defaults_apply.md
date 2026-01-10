# T-085 Apply instance_defaults in AST->NFIR conversion

## Task summary (DoD + verify)
- Apply `instance_defaults` during AST->NFIR conversion to create/augment nets.
- Emit warnings on default overrides unless the endpoint token uses `!inst.pin`.
- Suppress warnings when explicit binding matches the default.
- Ensure `$` nets introduced by defaults append to `port_order` after explicit `$` nets in `nets`.
- Add IR tests for overrides and port ordering.
- Verify: `pytest tests/unit_tests/ir/test_converter.py -v`

## Read
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md
- agents/adr/ADR-0007-instance-defaults.md
- src/asdl/ir/converters/ast_to_nfir.py
- tests/unit_tests/ir/test_converter.py

## Plan
- [ ] Review AST->NFIR conversion flow and existing instance binding logic.
- [ ] Apply instance_defaults to build/augment nets and port order.
- [ ] Emit override warnings with suppression rules; add tests.
- [ ] Verify converter tests and record results.

## Progress log
- 2026-01-12: Created scratchpad for T-085.

## Patch summary
- TBD.

## PR URL
- TBD.

## Verification
- TBD.

## Status request
- In progress.

## Blockers / Questions
- None.

## Next steps
- Implement instance_defaults behavior in AST->NFIR and add tests.
