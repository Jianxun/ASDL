# T-057 Pattern Expansion Engine

## Task summary
- DoD: Implement standalone pattern expansion per `docs/specs/spec_asdl_pattern_expansion.md` (ranges, alternation, splicing, expansion order, collisions, errors). Use `_` between basename and suffixes. Add focused unit tests for expansion and diagnostics; no pipeline integration.
- Verify: `venv/bin/pytest tests/unit_tests/parser -v`

## Read
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md
- docs/specs/spec_asdl_pattern_expansion.md
- src/asdl/ast/parser.py
- src/asdl/diagnostics/core.py
- src/asdl/diagnostics/codes.py
- src/asdl/ir/pipeline.py
- src/asdl/ir/converters/ast_to_nfir.py
- tests/unit_tests/parser/test_parser.py

## Plan
1. Implement standalone pattern expansion utility with diagnostics and limit checks.
2. Add parser-layer unit tests covering expansion order, splicing, and error cases.
3. Run parser tests and record results.

## Progress log
- Created feature branch `feature/T-057-pattern-expansion-engine`.
- Set T-057 status to in_progress in tasks_state.
- Added `src/asdl/patterns.py` expansion engine with diagnostics.
- Added unit tests in `tests/unit_tests/parser/test_pattern_expansion.py`.
- Ran parser unit tests.
- Set T-057 status to ready_for_review in tasks_state.
- Opened PR https://github.com/Jianxun/ASDL/pull/47.

## Patch summary
- agents/context/tasks_state.yaml: set T-057 to ready_for_review.
- agents/scratchpads/T-057_pattern_expansion_engine.md: capture progress, verification, and next steps.
- src/asdl/patterns.py: add pattern expansion engine with diagnostics and size checks.
- tests/unit_tests/parser/test_pattern_expansion.py: add expansion and diagnostics tests.

## Verification
- `venv/bin/pytest tests/unit_tests/parser -v` (passed)

## Status request
- Ready for review.

## Blockers / Questions
- None.

## Next steps
1. Wait for Reviewer feedback on PR #47.
