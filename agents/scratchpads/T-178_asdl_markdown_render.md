# Task summary (DoD + verify)
- Implement a Markdown renderer and generator script that emit the agreed layout (overview, interface ports/pins, variables, instances, nets with sections) from the extractor output.
- Provide a CLI that writes to a target directory.
- Add a short docs/asdl/README.md describing usage.
- Verify: venv/bin/python scripts/gen_asdl_docs.py examples/libs/sw_matrix/swmatrix_Tgate/swmatrix_Tgate.asdl --out /tmp/asdl-docs

# Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

# Plan
- Inspect existing docstring extractor output and any docs utilities to align renderer output.
- Add markdown renderer + tests, then add generator script + README.
- Verify via the task command and record results.

# Progress log
- Added Markdown renderer and table helpers for modules, nets, patterns, and interface docs.
- Added generator CLI script and README usage notes.
- Added markdown rendering tests for swmatrix_Tgate and full_switch_matrix.

# Patch summary
- src/asdl/docs/markdown.py + src/asdl/docs/__init__.py: render Markdown from AST + docstrings.
- scripts/gen_asdl_docs.py: CLI generator.
- docs/asdl/README.md: usage docs.
- tests/unit_tests/docs/test_markdown.py: renderer coverage.

# PR URL
- https://github.com/Jianxun/ASDL/pull/179

# Verification
- ./venv/bin/pytest tests/unit_tests/docs/test_markdown.py -v
- ./venv/bin/python scripts/gen_asdl_docs.py examples/libs/sw_matrix/swmatrix_Tgate/swmatrix_Tgate.asdl --out /tmp/asdl-docs

# Status request (Done / Blocked / In Progress)
- Done

# Blockers / Questions
- 

# Next steps
- Open PR and update task status to ready_for_review.
