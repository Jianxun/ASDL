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
- [x] Locate Sphinx domain depgraph build and config plumbing.
- [x] Implement `.asdlrc` discovery + config merge + lib_roots propagation.
- [x] Add/adjust unit test fixture for manifest + `.asdlrc` import resolution.
- [x] Update examples/docs/README.md note.
- [x] Run verify command.

# Progress log
- 2026-02-01 09:00 — Task intake and scope reviewed; read context/contract/task docs; next step set task status and branch.
- 2026-02-01 09:02 — Set T-255 status to in_progress and linted tasks_state; created feature branch; next step inspect Sphinx domain code.
- 2026-02-01 09:10 — Committed task kickoff metadata; files touched: agents/context/tasks_state.yaml, agents/scratchpads/T-255_sphinx_asdlrc.md; commit c8a8cdc; next step add Sphinx .asdlrc test coverage.
- 2026-02-01 09:18 — Added Sphinx manifest + .asdlrc unit test fixture; files touched: tests/unit_tests/docs/test_sphinx_asdlrc.py; commit cbcdcdf; next step implement .asdlrc handling in Sphinx domain.
- 2026-02-01 09:32 — Implemented .asdlrc discovery/merge for Sphinx depgraph builds; files touched: src/asdl/docs/sphinx_domain.py; commit 027332f; next step update docs note.
- 2026-02-01 09:35 — Documented .asdlrc support in examples/docs README; files touched: examples/docs/README.md; commit 1acd210; next step run verify tests.
- 2026-02-01 09:38 — Verified new Sphinx .asdlrc coverage; command `./venv/bin/pytest tests/unit_tests/docs/test_sphinx_asdlrc.py -v`; result: pass; next step finalize scratchpad and PR.

# Patch summary
- Added Sphinx .asdlrc-aware config path resolution, env merge, and lib_roots propagation for depgraph builds.
- Added Sphinx project manifest + .asdlrc unit test fixture to ensure imports resolve without AST-010.
- Documented .asdlrc lib_roots/env support in examples docs README.

# PR URL
- Pending.

# Verification
- ./venv/bin/pytest tests/unit_tests/docs/test_sphinx_asdlrc.py -v

# Status request
- In Progress

# Blockers / Questions
- None.

# Next steps
- Open PR and update tasks_state to ready_for_review.
