# Task summary (DoD + verify)
- Task: T-244 — Add ASDL Sphinx domain (Tier 1)
- DoD: Implement a minimal Sphinx domain that registers ASDL objects (doc, module, port, net, inst, var, pattern, import) with reference roles matching the agreed naming scheme. Provide registration entry points and stable target IDs without requiring Sphinx directives to parse ASDL files yet. Include minimal unit coverage for object registration and target naming.
- Verify: ./venv/bin/pytest tests/unit_tests/docs/test_sphinx_domain.py -v

# Read (paths)
- agents/roles/executor.md
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

# Plan
- Triage existing docs tooling and current asdl/docs modules.
- Draft unit tests for registration + target naming (TDD).
- Implement minimal Sphinx domain with object types/roles, registration entry points, and stable target IDs.
- Run verification.

# Progress log
- 2026-01-31 00:00 — Task intake and environment prep; reviewed contract/task files; created scratchpad and set task status to in_progress; next step: inspect existing docs tooling.
- 2026-01-31 00:02 — Task understanding: deliver a minimal ASDL Sphinx domain (object types + roles + stable target IDs) plus registration helpers and unit tests without requiring parsing ASDL files; next step: add tests.

# Patch summary

# PR URL

# Verification

# Status request (Done / Blocked / In Progress)

# Blockers / Questions

# Next steps
- 2026-01-31 00:05 — Added initial unit tests for ASDL Sphinx domain registration + target naming (TDD); files touched: tests/unit_tests/docs/test_sphinx_domain.py; next step: implement sphinx_domain module and exports.
- 2026-01-31 00:12 — Implemented ASDL Sphinx domain module with registration helpers, target naming, and fallback stubs; updated docs package exports; files touched: src/asdl/docs/sphinx_domain.py, src/asdl/docs/__init__.py; next step: run unit tests.
- 2026-01-31 00:14 — Commit b7ce713 (chore: start T-244 scratchpad); files: agents/context/tasks_state.yaml, agents/scratchpads/T-244_sphinx_domain.md; next step: add tests for Sphinx domain.
- 2026-01-31 00:15 — Commit 0c37df0 (test: cover ASDL sphinx domain helpers); files: tests/unit_tests/docs/test_sphinx_domain.py, agents/scratchpads/T-244_sphinx_domain.md; next step: implement Sphinx domain module.
