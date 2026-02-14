# T-276 - completion worker core

## Task summary (DoD + verify)
Implement a long-lived Python completion worker that reuses `src/asdl/ast/*`,
`src/asdl/imports/*`, and `.asdlrc` config loading semantics for endpoint,
imported symbol, and `param=` completion candidates. Completion context
detection must remain YAML-structure-aware.

Verify:
- `./venv/bin/pytest tests/unit_tests/tools/test_completion_worker.py -v`

## Read (paths)
- `agents/roles/executor.md`
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `docs/specs/spec_asdl_language_tools_extension.md`
- `agents/adr/ADR-0030-asdl-language-tools-extension.md`
- `src/asdl/ast/*`
- `src/asdl/imports/*`
- `src/asdl/cli/config.py`

## Plan
1. Add completion context detector for endpoint/import/param positions using YAML-aware heuristics.
2. Add semantic completion engine that loads docs with parser + import resolver and emits candidates.
3. Add stdio JSON worker protocol implementation with lifecycle methods and doc cache.
4. Add tests for completion engine and worker lifecycle.
5. Verify tests and finalize task state/PR handoff.

## Milestone notes
- Intake complete; task moved to `in_progress`.
- Added `asdl.tools.completion.context` YAML-aware context detector.
- Added `asdl.tools.completion.engine` that reuses AST parser, import resolver, and `.asdlrc` config loading.
- Implemented worker protocol in `extensions/asdl-language-tools/python/worker.py` (`initialize`, `update_document`, `complete`, `shutdown`).
- Added unit tests for semantic categories and worker lifecycle.

## Patch summary
- Added completion tooling package scaffolding:
  - `src/asdl/tools/__init__.py`
  - `src/asdl/tools/completion/__init__.py`
- Implemented YAML-structure-aware completion context detection:
  - `src/asdl/tools/completion/context.py`
- Implemented semantic completion engine with parser/import/config reuse:
  - `src/asdl/tools/completion/engine.py`
- Implemented long-lived NDJSON worker protocol:
  - `extensions/asdl-language-tools/python/worker.py`
- Added tests:
  - `tests/unit_tests/tools/test_completion_engine.py`
  - `tests/unit_tests/tools/test_completion_worker.py`

## PR URL
- Pending (will be created in closeout).

## Verification
- `./venv/bin/pytest tests/unit_tests/tools/test_completion_engine.py -v` (pass)
- `./venv/bin/pytest tests/unit_tests/tools/test_completion_worker.py -v` (pass)

## Status request (Done / Blocked / In Progress)
- In Progress

## Blockers / Questions
- None.

## Next steps
- Push branch and open PR.
- Set `T-276` to `ready_for_review` with PR number in `tasks_state`.
