# T-031 - ASDL_NFIR MVP Dialect + Conversion

## Task summary
- DoD: Implement MVP ASDL_NFIR dialect + verifiers; AST->NFIR conversion parses instance expr into `ref` + `params`, extracts `port_order` from `$` nets, carries devices/backends; unit tests for dialect + conversion.
- Verify: `pytest tests/unit_tests/ir`, `pytest tests/unit_tests/parser`

## Read
- `agents/roles/executor.md`
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.md`
- `agents/context/handoff.md`
- `docs/code_styles/xdsl_style.md`
- `docs/specs_mvp/spec_ast_mvp.md`
- `docs/specs_mvp/spec_asdl_nfir_mvp.md`
- `src/asdl/ast/models.py`
- `src/asdl/ast/parser.py`
- `tests/unit_tests/ir/test_dialect.py`
- `tests/unit_tests/ir/test_converter.py`

## Plan
1. Inspect existing IR/xdsl scaffolding and tests to anchor new dialect location and patterns.
2. Implement `asdl_nfir` dialect ops/attrs per MVP spec with verifiers.
3. Implement AST->NFIR conversion (instance expr parsing, port_order extraction, device/backend copy).
4. Add unit tests for dialect parsing/printing + conversion outputs.
5. Run verify commands and capture results.

## Progress log
- Read contract/specs and task context.
- Created feature branch `feature/T-031-nfir-mvp`.
- Marked T-031 as In Progress in `agents/context/tasks.md`.
- Added `asdl_nfir` dialect ops/attrs + verifiers with location support.
- Implemented AST->NFIR conversion with instance expr parsing and port order extraction.
- Replaced IR tests to cover NFIR dialect round-trip + converter output.
- Verified `pytest tests/unit_tests/ir` and `pytest tests/unit_tests/parser`.
- Opened PR https://github.com/Jianxun/ASDL/pull/27.
- Documented xDSL framework findings in `docs/code_styles/xdsl_style.md`.
- Tightened instance/endpoint parsing to reject invalid tokens, added top-name verifier, and added negative tests.
- Switched AST->NFIR conversion to emit diagnostics instead of raising exceptions.

## Patch summary
- `src/asdl/ir/__init__.py`: export AST->NFIR converter.
- `src/asdl/ir/converters/__init__.py`: package exports.
- `src/asdl/ir/converters/ast_to_nfir.py`: AST->NFIR conversion + helpers.
- `src/asdl/ir/nfir/dialect.py`: NFIR dialect ops/attrs + verifiers.
- `src/asdl/ir/nfir/__init__.py`: NFIR dialect exports.
- `tests/unit_tests/ir/test_dialect.py`: NFIR dialect verifier + roundtrip tests.
- `tests/unit_tests/ir/test_converter.py`: AST->NFIR conversion tests.
- `agents/context/handoff.md`: note NFIR completion and update next steps/tests.
- `agents/context/tasks.md`: mark T-031 Done and add PR link.
- `docs/code_styles/xdsl_style.md`: add xDSL framework notes for future agents.
- `src/asdl/ir/converters/ast_to_nfir.py`: reject invalid instance/endpoint tokens.
- `src/asdl/ir/nfir/dialect.py`: verify top module exists.
- `tests/unit_tests/ir/test_dialect.py`: add top validation test.
- `src/asdl/ir/converters/ast_to_nfir.py`: return diagnostics on invalid tokens.
- `tests/unit_tests/ir/test_converter.py`: expect diagnostics for invalid tokens.

## Verification
- `venv/bin/pytest tests/unit_tests/ir`
- `venv/bin/pytest tests/unit_tests/parser`

## Blockers / Questions
- None yet.

## Next steps
1. Update `agents/context/handoff.md` and `agents/context/tasks.md` for completion state.
2. Draft PR details once status is set to Done.
