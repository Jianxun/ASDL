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
- 
