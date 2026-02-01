# Task summary (DoD + verify)
- DoD: Always use the ASDL file stem as the page title (do not promote `document.top` or single-module names). Render `top` as a separate document-level "Top module" section placed after Overview and before Imports so it is visible without duplicating module titles. Update unit coverage to assert title selection and top-section rendering. Do not touch unrelated style docs (e.g., docs/code_styles/docstrings_comments.md).
- Verify: ./venv/bin/pytest tests/unit_tests/docs/test_sphinx_render.py -v

# Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

# Plan
- Inspect current title/overview/import rendering in sphinx_render.
- Update title selection to always use file stem and insert "Top module" section.
- Update tests to assert title selection and top section placement.
- Run verify command.

# Progress log
- 2026-02-01 00:00 — Task intake; updated scratchpad DoD/plan to match T-258; next step set task in_progress and branch.
- 2026-02-01 00:01 — Updated Sphinx render tests for file-stem titles and Top module section expectations; files touched: tests/unit_tests/docs/test_sphinx_render.py; next step commit tests then update renderer.
- 2026-02-01 00:02 — Committed task prep scratchpad/status updates (2c4968f); files touched: agents/context/tasks_state.yaml, agents/scratchpads/T-258_sphinx_title_dedupe.md; next step commit tests.
