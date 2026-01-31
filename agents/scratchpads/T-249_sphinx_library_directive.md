# Task summary (DoD + verify)
- DoD: Add a directory-capable directive or helper (e.g., `asdl:library`) that expands all `.asdl` files under a given directory and renders them in deterministic order. Update examples/docs to use the directive for `examples/libs` so Tier 2 docs build without pre-generated Markdown. Provide a small test for directory expansion ordering. Do not touch unrelated style docs (e.g., docs/code_styles/docstrings_comments.md).
- Verify: ./venv/bin/sphinx-build -b html examples/docs examples/docs/_build/html

# Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

# Plan
- Inspect existing Sphinx domain/directive implementation and current docs wiring.
- Implement directory-capable directive/helper and deterministic ordering.
- Add unit test for directory expansion ordering.
- Update examples/docs to use new directive for examples/libs.
- Run verify command.

# Progress log
- 2026-01-31 03:06 — Task intake; reviewed role instructions and task metadata; next step inspect Sphinx domain/docs.
- 2026-01-31 03:06 — Initialized scratchpad, set T-249 in_progress, ran tasks_state lint, created feature branch `feature/T-249-sphinx-library-directive`; next step implement helper + tests.

# Patch summary

# PR URL

# Verification

# Status request (Done / Blocked / In Progress)

# Blockers / Questions

# Next steps
