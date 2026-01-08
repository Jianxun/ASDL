# T-016 Diagnostic Core

## Task summary
- DoD: Implement diagnostic core types (Diagnostic, Severity, SourceSpan, Label, Note, FixIt), a collector sink, and text/JSON renderers with deterministic ordering.
- Verify: `pytest tests/unit_tests/diagnostics`.

## Read
- `agents/roles/executor.md`
- `agents/context/contract.md`
- `agents/context/tasks.md`
- `agents/context/handoff.md`
- `docs/specs/spec_diagnostics.md`
- `legacy/src/asdl/diagnostics.py`

## Plan
1. Create diagnostics package layout and core types matching spec and ordering rules.
2. Implement collector sink and text/JSON renderers.
3. Add centralized code registry and unit tests for ordering/rendering/serialization.
4. Update exports, task status/handoff, and run diagnostics tests.

## Progress log
- 2025-01-07: Created feature branch `feature/T-016-diagnostic-core` and committed `docs/specs/spec_diagnostics.md`.
- 2025-01-07: Read spec + context; set T-016 status to In Progress.
- 2025-01-07: Implemented diagnostics core package, collector, renderers, and centralized codes.
- 2025-01-07: Added diagnostics unit tests and ran `pytest tests/unit_tests/diagnostics`.
- 2025-01-07: Opened PR https://github.com/Jianxun/ASDL/pull/19.
- 2025-01-07: Tightened SourceSpan to require start/end; updated spec and tests accordingly.

## Patch summary
- `src/asdl/diagnostics/core.py`: added core diagnostic types and sorting helpers.
- `src/asdl/diagnostics/collector.py`: added collector sink for diagnostics.
- `src/asdl/diagnostics/renderers.py`: added text/JSON rendering utilities.
- `src/asdl/diagnostics/codes.py`: added centralized diagnostic code helpers.
- `src/asdl/diagnostics/__init__.py`: exported diagnostics API.
- `tests/unit_tests/diagnostics/test_sorting.py`: tests for ordering rules.
- `tests/unit_tests/diagnostics/test_renderers.py`: tests for text/JSON renderers.
- `agents/context/tasks.md`: updated T-016 status and PR link.
- `docs/specs/spec_diagnostics.md`: clarified missing-span behavior and text rendering.

## PR URL
- https://github.com/Jianxun/ASDL/pull/19

## Verification
- `venv/bin/python -m pytest tests/unit_tests/diagnostics`

## Blockers / Questions
- None.

## Next steps
1. Await Architect review on PR https://github.com/Jianxun/ASDL/pull/19.
