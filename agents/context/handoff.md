# Handoff

## Current state
- Refactor specs are canonical: `docs/specs/spec_ast.md` (pydantic AST) and `docs/specs/spec_asdl_ir.md` (xDSL IR) supersede ADR-0001 for view kinds (now {subckt, subckt_ref, primitive, dummy, behav}) and tighten dummy/subckt_ref/alias rules.
- ADR-0001 marked superseded; ADR-0002/0003 remain active. Contract updated accordingly.
- Branch `refactor-prep` created; ADR/spec edits committed previously. Current working tree has pending spec/context edits (to commit).
- Direction approved: clean rewrite pre-MVP with Pydantic v2 AST + locatable diagnostics, new xDSL IR; no backward-compatibility constraints.
- Tasks board updated with executor-ready rewrite tasks (T-010..T-015); earlier design tasks superseded.
- T-010 implementation started: new `src/asdl/ast/` Pydantic v2 AST models and `tests/unit_tests/ast` validation tests added; `pytest tests/unit_tests/ast` passing.
- T-011 planning complete; blocked on feature branch creation due to `.git` permission error (cannot lock ref). Task is a breaking rewrite; legacy parser should not be reused.
- T-016 diagnostic core merged to `main` with new diagnostics package, renderers, and unit tests; SourceSpan now requires start/end (no file-only spans).
- All non-AST code/tests archived under `legacy/`; active refactor code is only `src/asdl/ast/` and CLI scaffolding will be rebuilt.

## Last verified status
- `pytest tests/unit_tests/diagnostics` passing.

## Next steps (1–3)
1. Fix `.git` permissions or create the `feature/T-011-parser-locatable` branch for the executor.
2. Implement T-011 parser + LocationIndex rewrite and add `tests/unit_tests/parser_v2`.
3. Run `pytest tests/unit_tests/parser_v2` once implementation is complete.

## Risks / unknowns
- Legacy `context/todo_*.md` likely stale; avoid mixing with new board until reconciled.
- Dummy default semantics are backend-defined; lock deterministic defaults during implementation.
- Legacy generator/validator depend on old dataclasses; cleanup sequencing matters (T-015).
- Persistent `.git/index.lock` failures when creating branches; needs Architect investigation.
