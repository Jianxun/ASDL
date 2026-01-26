# T-232 — Add .asdlrc discovery + parsing utilities

## Task summary (DoD + verify)
- Implement a config loader that discovers `.asdlrc` by walking parents from an entry file directory, parses YAML schema_version 1, resolves relative paths against the rc directory, and expands `${ASDLRC_DIR}` and `${VAR}` tokens.
- Provide an API that returns rc `lib_roots`, `backend_config`, and an env map intended for merge into `os.environ`.
- Add unit tests for discovery, interpolation, and path resolution.
- Verify: `./venv/bin/pytest tests/unit_tests/cli -k asdlrc`

## Read (paths)
- agents/roles/executor.md
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

## Plan
- Add tests covering .asdlrc discovery, interpolation, and path resolution.
- Implement .asdlrc discovery + parsing utilities in CLI config module.
- Run targeted pytest for asdlrc tests.
- Summarize changes, update task state, and open PR.

## Progress log
- 2026-01-26 03:23 — Task intake; scratchpad created; next step update task state and branch.
- 2026-01-26 03:24 — Set T-232 status to in_progress; ran lint_tasks_state.py; created feature branch.
- 2026-01-26 03:27 — Added asdlrc config unit tests for discovery/interpolation/path resolution.
- 2026-01-26 03:28 — Implemented asdlrc discovery + parsing utilities with interpolation and path resolution.
- 2026-01-26 03:29 — Ran pytest for asdlrc tests (2 passed).
- 2026-01-26 03:30 — Commit 12c9ac9: chore: start T-232 asdlrc loader.
- 2026-01-26 03:31 — Commit acd973d: test: cover asdlrc discovery and expansion.
- 2026-01-26 03:31 — Commit 6ec8042: feat: add .asdlrc discovery and parsing.

## Patch summary
- Added .asdlrc config tests for discovery, interpolation, and path resolution.
- Implemented .asdlrc discovery and parsing utilities with env interpolation and rc-relative path resolution.

## PR URL
- TBD

## Verification
- ./venv/bin/pytest tests/unit_tests/cli -k asdlrc

## Status request
- In Progress

## Blockers / Questions
- None

## Next steps
- Update task state to in_progress, lint, create feature branch, then inspect existing CLI config code/tests.
