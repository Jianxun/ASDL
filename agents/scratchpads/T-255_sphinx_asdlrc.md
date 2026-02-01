# Task summary (DoD + verify)
- DoD: Update the Sphinx ASDL domain to discover `.asdlrc` for project builds (default to the project manifest directory, allow explicit config path override). Load lib_roots/env via `asdl.cli.config`, merge env values without overwriting existing OS variables, and pass resolved lib_roots into dependency-graph building. Add unit coverage that exercises a manifest + `.asdlrc` fixture and asserts import resolution succeeds without AST-010 errors. Update examples/docs/README.md to note that docs builds honor `.asdlrc` lib_roots/env. Do not touch unrelated style docs (e.g., docs/code_styles/docstrings_comments.md).
- Verify: ./venv/bin/pytest tests/unit_tests/docs/test_sphinx_asdlrc.py -v

# Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

# Plan
- Inspect Sphinx domain build hooks and depgraph integration points.
- Implement .asdlrc discovery + lib_roots plumbing for depgraph in the docs build.
- Add unit tests for manifest + .asdlrc fixture coverage.
- Update examples/docs README with .asdlrc usage note.
- Run verify command.

# Progress log
- 
