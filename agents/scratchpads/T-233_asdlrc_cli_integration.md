# T-233 — Wire .asdlrc into asdlc CLI (netlist + visualizer-dump)

## Task summary (DoD + verify)
- Add `--config` to the `asdlc` CLI and load `.asdlrc` based on each entry file.
- Merge rc `env` into `os.environ` only for missing keys, apply rc `lib_roots` after CLI `--lib` roots, and honor rc `backend_config` when `ASDL_BACKEND_CONFIG` is unset.
- Ensure `asdlc netlist` and `asdlc visualizer-dump` both use rc-derived library roots and backend config precedence.
- Add integration tests that exercise rc discovery and precedence across commands.
- Verify: `./venv/bin/pytest tests/unit_tests/cli -k asdlrc`

## Read (paths)
- agents/roles/executor.md
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

## Plan
- [x] Add CLI integration tests for rc discovery, env merge, lib roots, and backend config precedence.
- [x] Implement rc loading/merge helper and wire into netlist + visualizer-dump with `--config`.
- [x] Run targeted pytest.
- [x] Update scratchpad and task state; open PR.

## Progress log
- 2026-01-26 12:02 — Task intake; scratchpad created; next step create feature branch and outline tests.
- 2026-01-26 12:03 — Set T-233 status to in_progress; ran lint_tasks_state.py; created feature branch feature/T-233-asdlrc-cli.
- 2026-01-26 12:04 — Understanding: add --config handling and per-entry rc discovery in netlist + visualizer-dump, merge rc env for missing keys, append rc lib_roots after CLI libs, and use rc backend_config only when ASDL_BACKEND_CONFIG is unset; cover with integration tests.
- 2026-01-26 12:05 — Commit d80b628: chore: start T-233 asdlrc cli integration.
- 2026-01-26 12:10 — Added CLI integration tests for .asdlrc discovery, lib roots, env merge, and backend config precedence.
- 2026-01-26 12:10 — Commit a5cd91a: test: add asdlrc cli integration coverage.
- 2026-01-26 12:14 — Implemented rc loading/merging + --config wiring for netlist and visualizer-dump.
- 2026-01-26 12:14 — Commit 3d35970: feat: wire asdlrc into asdlc commands.
- 2026-01-26 12:15 — Ran ./venv/bin/pytest tests/unit_tests/cli -k asdlrc (passed).
- 2026-01-26 12:16 — Commit 9a2dc8a: chore: update T-233 scratchpad.
- 2026-01-26 12:17 — Pushed branch feature/T-233-asdlrc-cli.
- 2026-01-26 12:18 — Opened PR https://github.com/Jianxun/ASDL/pull/246.
- 2026-01-26 12:19 — Set T-233 status to ready_for_review; ran lint_tasks_state.py.
- 2026-01-26 12:20 — Commit 65337fd: chore: mark T-233 ready for review.
- 2026-01-26 12:21 — Pushed branch feature/T-233-asdlrc-cli (status update + scratchpad).

## Patch summary
- Added integration tests covering rc discovery, env merge, lib roots, and backend config precedence.
- Wired `--config` and rc-derived settings into `netlist` and `visualizer-dump` with env merge + backend config override rules.

## PR URL
- https://github.com/Jianxun/ASDL/pull/246

## Verification
- ./venv/bin/pytest tests/unit_tests/cli -k asdlrc

## Status request
- Ready for Review

## Blockers / Questions
- None

## Next steps
- Await reviewer feedback.
- 2026-01-26 13:00 — Review intake; confirmed PR target main and required artifacts present; set status to review_in_progress; next step inspect changes and tests.
