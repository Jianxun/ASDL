# T-177 — Implement comment-based docstring extractor

## Task summary (DoD + verify)
- DoD: Add a comment-preserving extractor that parses ASDL YAML with ruamel.yaml and yields docstrings for keys, inline comments, and section bundles. Expose a structured representation for Markdown rendering and add tests covering swmatrix_Tgate and full_switch_matrix bundle comments.
- Verify: `venv/bin/pytest tests/unit_tests/docs/test_docstrings.py -v`

## Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `docs/specs/spec_asdl_docs.md`
- `agents/adr/ADR-0021-asdl-docstrings-comments.md`
- `examples/libs/sw_matrix/swmatrix_Tgate/swmatrix_Tgate.asdl`
- `examples/libs/sw_matrix/full_switch_matrix_130_by_25/full_switch_matrix_130_by_25.asdl`

## Plan
- Add docstring extractor data structures and parsing helpers for block, inline, and section comments.
- Add tests for swmatrix_Tgate key/inline comments and full_switch_matrix bundle sections.
- Wire module exports in `src/asdl/docs/__init__.py`.

## Progress log
- Added unit tests for swmatrix_Tgate and full_switch_matrix section bundles.
- Implemented comment-based docstring extractor with key + section support.
- Verified docstring tests pass.

## Patch summary
- Added `src/asdl/docs` package with docstring extraction helpers and data structures.
- Added docstring extractor tests covering inline comments and section bundles.

## PR URL
- https://github.com/Jianxun/ASDL/pull/178

## Verification
- `venv/bin/pytest tests/unit_tests/docs/test_docstrings.py -v`

## Status request
- Ready for Review

## Blockers / Questions
- 

## Next steps
- Open PR and set task status to ready_for_review.
