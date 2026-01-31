# Task summary (DoD + verify)
- DoD: Add a docutils-node renderer that mirrors the Markdown layout for ASDL docs (overview, imports, per-module sections, interface/variables/instances/nets/patterns tables). The renderer must accept a parsed ASDL document + docstring index and return a top-level docutils node tree without depending on Sphinx runtime globals. Provide focused unit coverage for section/table structure and basic content wiring. Do not touch unrelated style docs (e.g., docs/code_styles/docstrings_comments.md).
- Verify: ./venv/bin/pytest tests/unit_tests/docs/test_sphinx_render.py -v

# Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

# Plan
- Triage existing markdown renderer + docstring extractor APIs to mirror structure in docutils nodes.
- Add unit tests for renderer section/table structure and content wiring.
- Implement sphinx_render docutils renderer + helpers.
- Verify with targeted pytest.

# Understanding
- Build a docutils-node renderer that mirrors the existing markdown layout for ASDL docs, taking a parsed ASDL document plus docstring index and returning a top-level docutils node tree without Sphinx globals; add unit tests for section/table structure and basic content wiring.

# Progress log

# Patch summary

# PR URL

# Verification

# Status request (Done / Blocked / In Progress)

# Blockers / Questions

# Next steps
# Progress log
- 2026-01-31 02:30 — Task intake: read contract/lessons/tasks/project status; created scratchpad; set T-247 to in_progress; ran lint; created feature branch `feature/T-247-sphinx-render`; next step: inspect existing markdown/docstring renderer.
- 2026-01-31 02:34 — Drafted unit tests for docutils renderer structure/content; added `tests/unit_tests/docs/test_sphinx_render.py`; next step: implement renderer.
- 2026-01-31 02:35 — Implemented docutils renderer in `src/asdl/docs/sphinx_render.py` and exported in `src/asdl/docs/__init__.py`; mirrored markdown layout with sections/tables/targets; next step: run pytest.
- 2026-01-31 02:36 — Ran `./venv/bin/pytest tests/unit_tests/docs/test_sphinx_render.py -v` (pass); updated tests to use `findall` to avoid docutils traverse warnings; next step: commit changes.
