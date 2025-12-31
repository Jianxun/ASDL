# Handoff

## Current state
- Refactor specs are canonical: `docs/specs/spec_ast.md` (pydantic AST) and `docs/specs/spec_asdl_ir.md` (xDSL IR) supersede ADR-0001 for view kinds (now {subckt, subckt_ref, primitive, dummy, behav}) and tighten dummy/subckt_ref/alias rules.
- ADR-0001 marked superseded; ADR-0002/0003 remain active. Contract updated accordingly.
- Branch `refactor-prep` created; ADR/spec edits committed previously. Current working tree has pending spec/context edits (to commit).
- Direction approved: clean rewrite pre-MVP with Pydantic v2 AST + locatable diagnostics, new xDSL IR; no backward-compatibility constraints.
- Tasks board updated with executor-ready rewrite tasks (T-010..T-015); earlier design tasks superseded.
- T-010 implementation started: new `src/asdl/ast/` Pydantic v2 AST models and `tests/unit_tests/ast` validation tests added; `pytest tests/unit_tests/ast` passing.
- T-011 implementation complete on `feature/T-011-parser-locatable`: new ruamel parser + LocationIndex + diagnostics mapping + parser tests; legacy parser not reused. PR: https://github.com/Jianxun/ASDL/pull/20.
- T-016 diagnostic core merged to `main` with new diagnostics package, renderers, and unit tests; SourceSpan now requires start/end (no file-only spans).
- All non-AST code/tests archived under `legacy/`; active refactor code is only `src/asdl/ast/` and CLI scaffolding will be rebuilt.

## Last verified status
- `pytest tests/unit_tests/parser` passing.

## Next steps (1–3)
1. Await review for PR https://github.com/Jianxun/ASDL/pull/20.
2. Proceed to T-012 after review approval.

## Risks / unknowns
- Legacy `context/todo_*.md` likely stale; avoid mixing with new board until reconciled.
- Dummy default semantics are backend-defined; lock deterministic defaults during implementation.
- Legacy generator/validator depend on old dataclasses; cleanup sequencing matters (T-015).
- None noted.
