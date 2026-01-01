# T-021 — ASDL_A Net-First AST MVP

## Task summary
- DoD: Rewrite ASDL_A (Tier-1) AST + parser for net-first explicit schema (explicit instances/nets only; no pattern sugar/imports/exports/inline binds); ports inferred only from `$` net keys; add parser/AST tests for MVP constraints.
- Verify: `pytest tests/unit_tests/parser`

## Read
- `agents/roles/executor.md`
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.md`
- `agents/context/handoff.md`
- `docs/specs/spec_ast.md`
- `docs/specs/spec_compiler_stack.md`
- `docs/specs/spec_asdl_nfir.md`
- `src/asdl/ast/models.py`
- `src/asdl/ast/parser.py`
- `src/asdl/ast/__init__.py`
- `src/asdl/__init__.py`
- `tests/unit_tests/parser/test_parser.py`

## Plan
1. Inspect current AST models/parser and existing parser tests to map deltas vs net-first spec.
2. Update AST models to the explicit net-first shape and tighten validation per MVP constraints.
3. Update parser to accept explicit instances/nets only (no sugar) and keep ordered maps.
4. Add/adjust parser + AST tests for MVP constraints and port inference rules; run verify.

## Progress log
- Read task/contract/spec context and created feature branch.
- Rewrote AST models to explicit net/instance schema and added validations for MVP constraints.
- Updated parser diagnostics to prefer key spans for key-level validation errors.
- Reworked parser tests to new schema and added AST validation tests.

## Patch summary
- `src/asdl/ast/models.py`: replace view-based AST with net-first explicit AST and MVP validators.
- `src/asdl/ast/parser.py`: prefer key spans for key-level validation errors.
- `src/asdl/ast/__init__.py`: update exports for new AST types.
- `src/asdl/__init__.py`: update exports for new AST types.
- `tests/unit_tests/parser/test_parser.py`: update parser tests to net-first schema.
- `tests/unit_tests/ast/test_models.py`: add AST validation tests for MVP constraints.

## Verification
- `venv/bin/python -m pytest tests/unit_tests/parser tests/unit_tests/ast`

## Blockers / Questions
- None.

## Next steps
- None.
