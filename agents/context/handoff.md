# Handoff

## Current state
- Refactor specs are canonical: `docs/specs/spec_ast.md` (pydantic AST) and `docs/specs/spec_asdl_cir.md` (xDSL IR) supersede ADR-0001 for view kinds (now {subckt, subckt_ref, primitive, dummy, behav}) and tighten dummy/subckt_ref/alias rules.
- ADR-0001 marked superseded; ADR-0002/0003 remain active; ADR-0004 accepted for NLIR dialect naming and `elab_state` usage. Contract updated accordingly.
- Branch `refactor-prep` created; ADR/spec edits committed previously. Current working tree has pending compiler-stack/NLIR doc edits (to commit).
- Direction approved: clean rewrite pre-MVP with Pydantic v2 AST + locatable diagnostics, new xDSL IR; no backward-compatibility constraints.
- Tasks board updated with executor-ready rewrite tasks (T-010..T-015); earlier design tasks superseded.
- T-010 implementation started: new `src/asdl/ast/` Pydantic v2 AST models and `tests/unit_tests/ast` validation tests added; `pytest tests/unit_tests/ast` passing.
- T-011 implementation complete on `feature/T-011-parser-locatable`: new ruamel parser + LocationIndex + diagnostics mapping + parser tests; legacy parser not reused. PR: https://github.com/Jianxun/ASDL/pull/20.
- T-016 diagnostic core merged to `main` with new diagnostics package, renderers, and unit tests; SourceSpan now requires start/end (no file-only spans).
- All non-refactor code/tests archived under `legacy/`; active refactor code is `src/asdl/ast/`, `src/asdl/diagnostics/`, and `src/asdl/ir/`.
- Port order is first-class and must propagate through NFIR/CIR/NLIR into emission; MVP passes are minimal/no-op.
- T-020 completed: IR dialect/converter sources restored under `src/asdl/ir/` and renamed to `asdl_cir` ops/attrs; IR tests added under `tests/unit_tests/ir/`.

## Last verified status
- `pytest tests/unit_tests/ir` passing.

## Next steps (1–3)
1. Await review for PR https://github.com/Jianxun/ASDL/pull/20.
2. Proceed to T-021 (AST net-first MVP parser/AST rewrite).
3. Use ADR-0004 guidance when implementing T-024 (NLIR dialect/lowering).

## Risks / unknowns
- Legacy `context/todo_*.md` likely stale; avoid mixing with new board until reconciled.
- Dummy default semantics are backend-defined; lock deterministic defaults during implementation.
- Legacy generator/validator depend on old dataclasses; cleanup sequencing matters (T-015).
- NLIR `elab_state` consistency checks and port-order propagation need explicit coverage in tests.
