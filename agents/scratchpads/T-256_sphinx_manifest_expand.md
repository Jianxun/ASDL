# Task summary (DoD + verify)
- DoD: Update the Sphinx project manifest workflow so each entry file expands to the full resolved import graph (entries + imported files). Generated stub pages and the project toctree must include all resolved files in deterministic order, with duplicates removed. Import resolution must use the same lib_roots/.asdlrc handling as depgraph builds. Add unit coverage to assert auto-expansion from a minimal manifest that only lists a top file, and that imported files appear in the generated list. Do not touch unrelated style docs (e.g., docs/code_styles/docstrings_comments.md).
- Verify: ./venv/bin/pytest tests/unit_tests/docs/test_sphinx_project_pages.py -v

# Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

# Plan
- Inspect project manifest parsing and stub generation in Sphinx domain.
- Add import-graph expansion for manifest entries using shared resolver settings.
- Update tests to cover auto-expansion and deterministic ordering.
- Run verify command.

# Progress log
- 
