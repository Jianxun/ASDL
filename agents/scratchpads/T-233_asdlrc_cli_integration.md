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
- Add CLI integration tests for rc discovery, env merge, lib roots, and backend config precedence.
- Implement rc loading/merge helper and wire into netlist + visualizer-dump with `--config`.
- Run targeted pytest.
- Update scratchpad and task state; open PR.

## Progress log
- 2026-01-26 12:02 — Task intake; scratchpad created; next step create feature branch and outline tests.

## Patch summary

## PR URL

## Verification

## Status request

## Blockers / Questions

## Next steps
- 2026-01-26 12:03 — Set T-233 status to in_progress; ran lint_tasks_state.py; created feature branch feature/T-233-asdlrc-cli.
- 2026-01-26 12:04 — Understanding: add --config handling and per-entry rc discovery in netlist + visualizer-dump, merge rc env for missing keys, append rc lib_roots after CLI libs, and use rc backend_config only when ASDL_BACKEND_CONFIG is unset; cover with integration tests.
