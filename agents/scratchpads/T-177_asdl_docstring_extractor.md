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
- 

## Patch summary
- 

## PR URL
- 

## Verification
- 

## Status request
- In Progress

## Blockers / Questions
- 

## Next steps
- 
