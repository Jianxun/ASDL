# Task summary (DoD + verify)
- DoD: Update Sphinx doc rendering to (1) remove `kind` and `direction` columns from the Interface/Ports table, leaving only `name` and `description`, and (2) move the Patterns section above other module tables so pattern definitions appear first. Add or update unit coverage to assert the interface table headers and section ordering. Do not touch unrelated style docs (e.g., docs/code_styles/docstrings_comments.md).
- Verify: ./venv/bin/pytest tests/unit_tests/docs/test_sphinx_render.py -v

# Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

# Plan
- Inspect current module rendering order and table headers in sphinx_render.
- Update interface table headers and section ordering.
- Adjust tests to assert new headers/ordering.
- Run verify command.

# Progress log
- 2026-02-01 02:43 — Task intake and scope confirmed (T-257); reviewed workflow/docs; next step update task status and branch.
- 2026-02-01 02:43 — Set T-257 status to in_progress and ran lint; files touched: agents/context/tasks_state.yaml; next step create feature branch.
- 2026-02-01 02:43 — Created feature branch feature/T-257-sphinx-table-order; next step inspect Sphinx render tables/tests.
- 2026-02-01 02:44 — Updated Sphinx render tests to expect interface headers without kind/direction and assert patterns section ordering; file touched: tests/unit_tests/docs/test_sphinx_render.py; next step adjust renderer.
- 2026-02-01 02:44 — Moved patterns section ahead of other module tables and trimmed interface headers/rows; file touched: src/asdl/docs/sphinx_render.py; next step run unit tests.
- 2026-02-01 02:45 — Ran ./venv/bin/pytest tests/unit_tests/docs/test_sphinx_render.py -v; result: passed; next step commit changes.
