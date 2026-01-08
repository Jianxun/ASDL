# T-043 Endpoint Lists (Lists Only)

## Task summary
- DoD: Implement list-only endpoint authoring (disallow string endpoint lists) per ADR-0005; update AST schema, parser validation, and converters; update diagnostics to guide users; adjust tests.
- Verify: `pytest tests/unit_tests/parser` and `pytest tests/unit_tests/ir`.

## Read
- agents/context/contract.md
- agents/context/handoff.md
- agents/context/tasks.md
- agents/scratchpads/T-043_endpoint_list_lists_only.md
- docs/specs_mvp/spec_ast_mvp.md
- src/asdl/ast/models.py
- src/asdl/ast/parser.py
- src/asdl/ir/converters/ast_to_nfir.py
- tests/unit_tests/ast/test_models.py
- tests/unit_tests/parser/test_parser.py
- tests/unit_tests/ir/test_converter.py
- tests/unit_tests/e2e/test_pipeline_mvp.py
- tests/unit_tests/cli/test_netlist.py

## Plan
- Update AST models to require list-only endpoints and add a validation message for string endpoints.
- Update AST->NFIR conversion for list endpoints; update tests/fixtures to use YAML lists.
- Add parser test for list-only enforcement; run parser + IR tests.

## Progress log
- 2026-01-02: Created branch `feature/T-043-endpoint-list-only`, set task to In Progress, initialized scratchpad.
- 2026-01-02: Updated AST endpoint list type/validation and AST->NFIR parsing; refreshed tests/fixtures for list-only endpoints and added parser coverage.
- 2026-01-02: Removed converter exceptions in endpoint/instance parsing; return diagnostics instead.

## Patch summary
- `src/asdl/ast/models.py`: enforce list-only endpoint lists with a validator message.
- `src/asdl/ir/converters/ast_to_nfir.py`: parse list-based endpoints without raising; return diagnostics on errors.
- `tests/unit_tests/ast/test_models.py`: update nets fixtures to list syntax.
- `tests/unit_tests/parser/test_parser.py`: update YAML fixtures for list endpoints, add list-only error test, adjust line expectations.
- `tests/unit_tests/ir/test_converter.py`: update nets fixtures to list syntax.
- `tests/unit_tests/e2e/test_pipeline_mvp.py`: update nets fixtures to list syntax.
- `tests/unit_tests/cli/test_netlist.py`: update nets fixtures to list syntax.

## PR URL
- https://github.com/Jianxun/ASDL/pull/32

## Verification
- `venv/bin/pytest tests/unit_tests/parser` (pass)
- `venv/bin/pytest tests/unit_tests/ir` (pass)

## Blockers / Questions
- 

## Next steps
- Await review on PR https://github.com/Jianxun/ASDL/pull/32.
