# T-251: Add asdlc depgraph-dump command

## Task summary (DoD + verify)
- DoD: Add an `asdlc depgraph-dump` CLI command that accepts one or more entry ASDL files, builds the dependency graph, and writes JSON to a user-supplied path (stdout if omitted). Command must surface diagnostics and exit non-zero on errors. Include a CLI test that asserts output schema, including presence of `module_id` fields. Do not touch unrelated style docs (e.g., docs/code_styles/docstrings_comments.md).
- Verify: `./venv/bin/pytest tests/unit_tests/cli/test_depgraph_dump.py -v`

## Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md
- src/asdl/cli/__init__.py
- src/asdl/docs/depgraph.py

## Plan
- [x] Inspect existing CLI structure and depgraph helpers.
- [x] Add depgraph-dump command wiring and error handling.
- [x] Add CLI test for JSON schema and module_id fields.
- [x] Run targeted tests.

## Progress log
- 2026-01-31 21:29 — Task intake; reviewed task card/contract/lessons/project status; created scratchpad and set T-251 in_progress; next step: inspect CLI/depgraph helpers.
- 2026-01-31 21:30 — Reviewed CLI and depgraph helpers to align new command with existing diagnostics/output conventions.
- 2026-01-31 21:32 — Added depgraph CLI test and confirmed failure (missing command); next step: implement depgraph-dump CLI.
- 2026-01-31 21:32 — Implemented depgraph-dump CLI wiring with rc/lib resolution, JSON output, and diagnostics handling in src/asdl/cli/__init__.py.
- 2026-01-31 21:33 — Ran depgraph CLI test (./venv/bin/pytest tests/unit_tests/cli/test_depgraph_dump.py -v); passed.
- 2026-01-31 21:34 — Commit 3376ff3: "test: add depgraph dump CLI schema check".
- 2026-01-31 21:34 — Commit f39e3b1: "feat: add depgraph-dump CLI command".
- 2026-01-31 21:35 — Opened PR https://github.com/Jianxun/ASDL/pull/267.
- 2026-01-31 21:35 — Set T-251 status to ready_for_review and ran scripts/lint_tasks_state.py.

## Patch summary
- Added depgraph-dump CLI command with rc/lib resolution, JSON output, and diagnostics handling.
- Added CLI test validating depgraph JSON schema and module_id fields.

## PR URL
https://github.com/Jianxun/ASDL/pull/267

## Verification
- ./venv/bin/pytest tests/unit_tests/cli/test_depgraph_dump.py -v

## Status request
Ready for review.

## Blockers / Questions
None.

## Next steps
Await review.
