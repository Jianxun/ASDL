# T-010 — AST Pydantic v2

## Task summary
- Implement Pydantic v2 AST models aligned with `agents/specs/spec_ast.md`.
- Enforce AST hard requirements (non-empty templates, dummy name/kind coupling, conns mapping).
- Add `model_json_schema` export.
- Add focused unit tests for validation edge cases.
- Verify: `pytest tests/unit_tests/ast`.

## Read
- `agents/specs/spec_ast.md`
- `agents/specs/spec_asdl_ir.md`
- `agents/context/contract.md`
- `agents/context/tasks.md`
- `agents/context/handoff.md`
- `agents/roles/executor.md`

## Plan
1. Implement new AST package under `src/asdl/ast/` from scratch.
2. Add validators and discriminated unions per spec.
3. Add JSON schema export and public exports.
4. Add unit tests in `tests/unit_tests/ast/`.
5. Run `pytest tests/unit_tests/ast` and update handoff/tasks.

## Progress log
- 2025-01-05: Marked task In Progress; set up plan and scratchpad.
- 2025-01-05: Implemented Pydantic v2 AST models under `src/asdl/ast/` and added unit tests.

## Patch summary
- `src/asdl/ast/models.py`: new Pydantic v2 AST models with discriminated `ViewDecl` and validators.
- `src/asdl/ast/__init__.py`: public exports and `model_json_schema` helper.
- `tests/unit_tests/ast/test_ast_models.py`: validation edge-case coverage for AST requirements.

## Verification
- `venv/bin/pytest tests/unit_tests/ast` (pass)

## Blockers / Questions
- Investigate persistent `.git/index.lock` errors (Architect).

## Next steps
1. Create `src/asdl/ast/` models and exports.
2. Add tests under `tests/unit_tests/ast/`.
