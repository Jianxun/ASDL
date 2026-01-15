# T-129 GraphIR pattern origin attributes and table

## Task summary (DoD + verify)
- Add typed `graphir.pattern_origin` attr, attach to net/instance/endpoint ops, define module attrs `pattern_expression_table`.
- Update GraphIR spec to describe atomized-only provenance model.
- Verify: none listed.

## Read
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md
- agents/adr/ADR-0015-graphir-pattern-metadata.md

## Plan
- Add GraphIR typed pattern_origin attribute + helpers and wire into ops + module attrs.
- Update spec text to reflect atomized-only provenance and module table.
- Validate updates with lint/tests if applicable and record results.

## Progress log
- 2026-01-14: Set T-129 to in_progress, created feature branch.

## Patch summary
- Added GraphIR pattern_origin typed attr + coercion helpers, optional attrs on net/instance/endpoint, and module pattern_expression_table support with verification.
- Updated GraphIR spec to document atomized-only provenance and expression table.
- Added GraphIR structure tests for pattern origin and expression table behavior.

## PR URL
- https://github.com/Jianxun/ASDL/pull/137

## Verification
- `./venv/bin/python -m pytest tests/unit_tests/ir/test_graphir_structure.py`

## Status request
- Ready for Review

## Blockers / Questions
- None yet.

## Next steps
- Open PR and update task state to ready_for_review.
