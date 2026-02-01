# Task summary (DoD + verify)
- DoD: Update the Sphinx ASDL domain to discover `.asdlrc` for project builds (default to the project manifest directory, allow explicit config path override). Load lib_roots/env via `asdl.cli.config`, merge env values without overwriting existing OS variables, and pass resolved lib_roots into dependency-graph building. Add unit coverage that exercises a manifest + `.asdlrc` fixture and asserts import resolution succeeds without AST-010 errors. Update examples/docs/README.md to note that docs builds honor `.asdlrc` lib_roots/env. Do not touch unrelated style docs (e.g., docs/code_styles/docstrings_comments.md).
- Verify: ./venv/bin/pytest tests/unit_tests/docs/test_sphinx_asdlrc.py -v

# Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

# Plan
- Inspect Sphinx domain build hooks and depgraph integration points.
- Implement .asdlrc discovery + lib_roots plumbing for depgraph in the docs build.
- Add unit tests for manifest + .asdlrc fixture coverage.
- Update examples/docs README with .asdlrc usage note.
- Run verify command.

# Understanding
- Ensure Sphinx ASDL domain uses `.asdlrc` (auto-discover near project manifest or explicit override) to load lib_roots/env via `asdl.cli.config`, merge env vars without clobbering existing OS env, and pass resulting lib_roots into depgraph so imports resolve without AST-010. Add fixture-backed unit test and doc note.

# Todo
- [ ] Locate Sphinx domain depgraph build and config plumbing.
- [ ] Implement `.asdlrc` discovery + config merge + lib_roots propagation.
- [ ] Add/adjust unit test fixture for manifest + `.asdlrc` import resolution.
- [ ] Update examples/docs/README.md note.
- [ ] Run verify command.

# Progress log
- 2026-02-01 09:00 — Task intake and scope reviewed; read context/contract/task docs; next step set task status and branch.
- 2026-02-01 09:02 — Set T-255 status to in_progress and linted tasks_state; created feature branch; next step inspect Sphinx domain code.
