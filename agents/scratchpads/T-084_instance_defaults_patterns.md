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
- docs/specs/spec_ast.md
- src/asdl/ast/models.py
- src/asdl/ast/parser.py
- tests/unit_tests/ast/test_models.py
- tests/unit_tests/parser/test_parser.py

## Plan
- [x] Review current AST models and parser handling for module fields.
- [x] Add schema fields and validation for `patterns` + `instance_defaults` shapes.
- [x] Update parser to parse module-local `patterns` and `instance_defaults`.
- [x] Add AST and parser tests for valid/invalid shapes and module-local-only behavior.

## Progress log
- 2026-01-12: Created scratchpad for T-084.
- 2026-01-12: Set T-084 status to in_progress and created feature branch.
- 2026-01-12: Added AST schema validation for patterns + instance_defaults.
- 2026-01-12: Added AST/parser tests for patterns/instance_defaults shapes and module-local-only behavior.
- 2026-01-12: Verified AST and parser unit tests.

## Patch summary
- Added module-level `patterns`/`instance_defaults` schema fields with shape validation.
- Added AST/parser coverage for valid and invalid pattern/default shapes and module-local-only enforcement.

## PR URL
- https://github.com/Jianxun/ASDL/pull/90

## Verification
- `./venv/bin/pytest tests/unit_tests/ast -v`
- `./venv/bin/pytest tests/unit_tests/parser -v`

## Status request
- In progress.

## Blockers / Questions
- None.

## Next steps
- Open PR and request review.
