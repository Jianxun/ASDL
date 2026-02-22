# T-294 - Enforce decorated module symbol grammar in AST parse/schema

## Task summary (DoD + verify)
- Enforce `cell` / `cell@view` grammar for module symbols during AST schema/parse validation.
- Reject malformed forms (`@view`, `cell@`, `cell@view@extra`) at parse/schema stage.
- Cover both module declaration names and instance references.
- Verify with: `./venv/bin/pytest tests/unit_tests/ast/test_models.py tests/unit_tests/parser/test_parser.py -k "view or decorated or module symbol" -v`

## Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `agents/roles/executor.md`
- `docs/specs/spec_asdl_views.md`
- `src/asdl/ast/models.py`
- `src/asdl/ast/parser.py`
- `tests/unit_tests/ast/test_models.py`
- `tests/unit_tests/parser/test_parser.py`

## Plan
1. Add targeted negative tests for malformed decorated module symbols in models and parser suites.
2. Implement shared symbol grammar validation in AST models for module keys and instance references.
3. Run targeted verification and close out state/PR metadata.

## Milestone notes
- Added parser/model negative cases for invalid decorated symbols across module declarations and both instance authoring forms.
- Implemented schema-level module symbol validator and inline instance reference validation.
- Verified targeted suites and corrected malformed `-k` expression for executable filter coverage.

## Patch summary
- Added AST model tests that reject malformed module declaration names and malformed structured/inline instance references.
- Added parser tests that ensure malformed decorated symbols fail with parse diagnostics.
- Added shared module symbol grammar validation (`cell` / `cell@view`) and applied it to:
  - `AsdlDocument.modules` keys
  - `InstanceDecl.ref`
  - inline instance expressions via `ModuleDecl.instances` validation

## PR URL
- Pending PR creation in closeout.

## Verification
- `./venv/bin/pytest tests/unit_tests/ast/test_models.py tests/unit_tests/parser/test_parser.py -v` -> pass (54 passed)
- `./venv/bin/pytest tests/unit_tests/ast/test_models.py tests/unit_tests/parser/test_parser.py -k "view or decorated or module symbol" -v` -> fails due invalid pytest expression in task command (`module symbol` adjacency)
- `./venv/bin/pytest tests/unit_tests/ast/test_models.py tests/unit_tests/parser/test_parser.py -k "view or decorated or module or symbol" -v` -> pass (29 passed, 25 deselected)

## Status request
- In Progress (moving to Ready for Review during PR closeout)

## Blockers / Questions
- Task verify command uses an invalid pytest `-k` expression; used the closest executable expression for proof.

## Next steps
- Push branch and open PR to `main`.
- Update `tasks_state.yaml` to `ready_for_review` with PR number and run tasks-state linter.
