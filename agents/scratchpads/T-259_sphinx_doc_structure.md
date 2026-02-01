# Task summary (DoD + verify)
- DoD: Render document titles as the ASDL file name with extension (e.g., `inv.asdl`) and treat Imports as a file-level section. Ensure the file Overview uses only file-level docstrings. Module-level overviews must be labeled "Notes" (not "Overview") to avoid confusion with file-level Overview. Update unit coverage to assert title selection and section ordering. Do not touch unrelated style docs (e.g., docs/code_styles/docstrings_comments.md).
- Verify: ./venv/bin/pytest tests/unit_tests/docs/test_sphinx_render.py -v

# Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

# Plan
- Inspect document title + section rendering in sphinx_render.
- Implement file-name titles and rename module overview to "Notes".
- Ensure file-level Overview/Imports remain separate from module sections.
- Update tests to assert title selection and section ordering.
- Run verify command.

# Progress log
- 
