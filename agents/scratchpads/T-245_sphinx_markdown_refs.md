# Task summary (DoD + verify)
- DoD: Extend Markdown rendering to emit MyST directives/labels that register ASDL objects with the Sphinx domain (module, port, net, inst, var, pattern, import, doc). Ensure cross-ref names follow the agreed scheme (module::name, module::$port, file::alias) and keep output Markdown valid for current docs. Add unit coverage asserting the emitted directives/labels for swmatrix_Tgate_doc. Do not touch unrelated style docs (e.g., docs/code_styles/docstrings_comments.md).
- Verify: ./venv/bin/pytest tests/unit_tests/docs/test_markdown_sphinx_refs.py -v

# Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

# Plan
- Inspect current Markdown rendering and existing tests for doc output.
- Update renderer to emit MyST labels/directives for ASDL objects with agreed naming scheme.
- Add/adjust unit tests for swmatrix_Tgate_doc to assert emitted directives/labels.
- Run verify command.
## Todo
- [x] Add tests for MyST directives/labels in swmatrix_Tgate_doc output.
- [ ] Update Markdown renderer to emit ASDL domain directives/labels.
- [ ] Run verify command.

# Progress log

# Patch summary

# PR URL

# Verification

# Status request (Done / Blocked / In Progress)

# Blockers / Questions

# Next steps
- 2026-01-31 00:00 — Task intake; confirmed T-245 ready; read contract/lessons/project_status; next step inspect markdown renderer + tests.
- 2026-01-31 00:00 — Added unit test for MyST directives/labels in swmatrix_Tgate doc output; files touched: tests/unit_tests/docs/test_markdown_sphinx_refs.py; next step update markdown renderer.
