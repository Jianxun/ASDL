# T-181 Pattern Service

## Task summary (DoD + verify)
- Build pure pattern service modules for parsing PatternExpr, named pattern substitution, expansion, and binding (named-axis broadcast).
- Add tests for splice flattening, endpoint expansion, and axis broadcast mismatches.
- Verify: `venv/bin/pytest tests/unit_tests/patterns_refactor -v`

## Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `docs/specs_refactor/spec_refactor_pattern_service.md`

## Plan
- [ ] Add tests for pattern parsing/expansion/binding requirements.
- [ ] Implement pattern service modules with parsing, expansion, and binding logic.
- [ ] Wire exports and verify tests.

## Progress log
- Created scratchpad and captured DoD.
- Added initial pattern service tests for splice flattening, endpoint expansion, and axis mismatch.
- Implemented parser, expansion, and binding helpers for refactor pattern service.

## Patch summary
- Added tests for pattern service expectations.
- Added refactor pattern service modules for parsing, expansion, and binding.

## PR URL
- TBD

## Verification
- `venv/bin/pytest tests/unit_tests/patterns_refactor -v`

## Status request
- In Progress

## Blockers / Questions
- None.

## Next steps
- Implement pattern service parsing/expansion/binding modules to satisfy tests.
