# Task summary (DoD + verify)
- DoD: Add Sphinx config that loads the ASDL domain and MyST parser, includes generated Markdown docs under docs/asdl in the toctree, and documents the build entrypoint. Provide a requirements file or pyproject extras to install sphinx + myst-parser. Add a smoke doc build command that runs on the generated docs set. Do not touch unrelated style docs (e.g., docs/code_styles/docstrings_comments.md).
- Verify: ./venv/bin/sphinx-build -b html docs docs/_build/html

# Read (paths)

# Plan

# Progress log

# Patch summary

# PR URL

# Verification

# Status request (Done / Blocked / In Progress)

# Blockers / Questions

# Next steps
## Read (paths)
- agents/roles/executor.md
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

## Plan
- Inspect existing docs config and ASDL docs layout.
- Add Sphinx config + requirements/extras, update toctree, and document build entrypoint.
- Add/adjust smoke build command (documented) and ensure docs/asdl content included.
- Run verify command and update scratchpad with results.

## Progress log
- 2026-01-31 00:00 — Task intake; read role/contract/task files; created scratchpad; set T-246 to in_progress; next: inspect docs config.
