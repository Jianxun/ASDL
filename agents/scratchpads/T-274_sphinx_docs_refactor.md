# Task summary (DoD + verify)
- DoD: Split Sphinx docs responsibilities so sphinx_domain.py only holds the Sphinx domain/directives/app hooks, moving manifest parsing + project page generation into a new module and rendering helpers from sphinx_render.py into a dedicated helper module. Keep public APIs and behavior stable (no doc output changes). Update imports/__all__ and ensure doc tests still pass.
- Verify: ./venv/bin/pytest tests/unit_tests/docs -v

# Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md
- agents/context/codebase_map.md

# Plan
- Identify responsibilities to extract from sphinx_domain.py and sphinx_render.py.
- Create helper modules and move code with minimal surface changes.
- Update imports, __all__, and any references.
- Run verify command.

# Progress log
- 2026-02-05 — Task created.
