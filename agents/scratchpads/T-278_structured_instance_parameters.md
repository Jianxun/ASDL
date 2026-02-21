# T-278 - structured instance `parameters`

## Task summary
- DoD:
  - Extend AST models/parsing to allow instance entries as either legacy inline
    strings or structured objects with `ref` and optional `parameters`.
  - Treat `parameters` as canonical and reject `params` alias in structured
    instances.
  - Preserve source location metadata for structured instance values.
  - Keep backward compatibility for existing inline strings.

## Verify
- `./venv/bin/pytest tests/unit_tests/ast -v`
- `./venv/bin/pytest tests/unit_tests/parser/test_parser.py -v`

## Read
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `agents/adr/ADR-0031-instance-parameter-syntax.md`
- `docs/specs/spec_ast.md`
- `src/asdl/ast/models.py`
- `src/asdl/ast/parser.py`
- `tests/unit_tests/ast/test_models.py`
- `tests/unit_tests/parser/test_parser.py`

## Plan
1. Add `InstanceDecl` structured AST model and dual-form `instances` typing.
2. Reject `params` alias for structured instance objects.
3. Preserve location metadata for structured instance `ref`/`parameters` values.
4. Add regression tests for acceptance, rejection, and span attachment.
5. Run task verify commands.

## Milestone notes
- Intake: confirmed `T-278` status `ready`; set `in_progress` and linted task state.
- Implementation: added dual-form instance support with structured-location tracking.
- Verification: AST and parser tests pass with structured-instance regression cases.

## Patch summary
- Added AST `InstanceDecl` (`ref` + optional `parameters`) and `InstanceValue`
  union support for module `instances`.
- Enforced canonical `parameters` key by rejecting structured `params` alias.
- Extended parser location attachment for structured instance values:
  instance `ref`, `parameters` block, and per-parameter value locations.
- Added/updated unit tests in AST and parser suites for:
  - structured instance acceptance
  - structured `params` alias rejection
  - structured instance source-location preservation

## PR URL
- Pending

## Verification
- `./venv/bin/pytest tests/unit_tests/ast tests/unit_tests/parser/test_parser.py -v` (pass)

## Status request
- In Progress

## Blockers / Questions
- None

## Next steps
1. Commit implementation and tests.
2. Push branch and open PR to `main`.
3. Set task state to `ready_for_review` with PR number and lint task state.
