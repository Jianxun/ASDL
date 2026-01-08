# T-030 AST + Parser MVP Refactor

## Task summary
- DoD: Rewrite AST + parser for MVP spec `docs/specs_mvp/spec_ast_mvp.md` (AsdlDocument with only `top/modules/devices`; `ModuleDecl` with `instances`/`nets` ordered maps of raw strings; `DeviceDecl` + `DeviceBackendDecl` with required template; enforce hard requirements and forbid legacy fields like ports/views/imports/exports; update `src/asdl/ast/__init__.py` exports + JSON schema); refresh parser/location tests for new schema and add AST validation tests.
- Verify: `pytest tests/unit_tests/parser` and `pytest tests/unit_tests/ast`.

## Read
- `agents/roles/executor.md`
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.md`
- `agents/context/handoff.md`
- `docs/specs_mvp/spec_ast_mvp.md`
- `src/asdl/ast/models.py`
- `src/asdl/ast/__init__.py`
- `src/asdl/ast/parser.py`
- `src/asdl/ast/location.py`
- `src/asdl/__init__.py`
- `tests/unit_tests/parser/test_parser.py`

## Plan
1. Inspect current AST models/parser and tests to identify required changes and stale coverage.
2. Update AST models to match MVP spec and hard requirements; adjust exports/schema.
3. Update parser to align with schema, preserve ordering, and update location handling.
4. Refresh/trim parser and AST tests; remove stale cases; add MVP validation tests.
5. Run required tests and update handoff/tasks.

## Progress log
- Initialized scratchpad with required sections.
- Rewrote AST models and exports for MVP schema; updated top-level package exports.
- Replaced stale parser tests; added AST model validation tests; fixed location assertions.
- Ran required parser and AST tests.
- Opened PR https://github.com/Jianxun/ASDL/pull/26.

## Patch summary
- `src/asdl/ast/models.py`: replaced legacy AST classes with MVP-only models and validators.\n+- `src/asdl/ast/__init__.py`: updated exports for MVP AST types.\n+- `src/asdl/__init__.py`: aligned top-level exports with MVP AST types.\n+- `tests/unit_tests/parser/test_parser.py`: replaced legacy parser tests with MVP cases and new location checks.\n+- `tests/unit_tests/ast/test_models.py`: added MVP AST validation tests.

## PR URL
- https://github.com/Jianxun/ASDL/pull/26

## Verification
- `venv/bin/pytest tests/unit_tests/parser`\n+- `venv/bin/pytest tests/unit_tests/ast`

## Blockers / Questions
- None yet.

## Next steps
1. Await Architect review for T-030 PR.
