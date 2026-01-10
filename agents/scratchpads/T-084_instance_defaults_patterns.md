# T-084 AST schema for instance_defaults + patterns

## Task summary (DoD + verify)
- Add module-level `patterns` and `instance_defaults` to AST schema and parser.
- Enforce shape validation for pattern entries and default binding maps.
- Add parser/AST tests for valid and invalid shapes (module-local-only behavior, required `bindings` map).
- Verify: `pytest tests/unit_tests/ast -v`
- Verify: `pytest tests/unit_tests/parser -v`

## Read
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md
- agents/adr/ADR-0007-instance-defaults.md
- agents/adr/ADR-0008-named-patterns.md

## Plan
- [ ] Review current AST models and parser handling for module fields.
- [ ] Add schema fields and validation for `patterns` + `instance_defaults` shapes.
- [ ] Update parser to parse module-local `patterns` and `instance_defaults`.
- [ ] Add AST and parser tests for valid/invalid shapes and module-local-only behavior.

## Progress log
- 2026-01-12: Created scratchpad for T-084.

## Patch summary
- TBD

## PR URL
- TBD

## Verification
- TBD

## Status request
- In progress.

## Blockers / Questions
- None.

## Next steps
- Implement schema/parser updates and tests.
