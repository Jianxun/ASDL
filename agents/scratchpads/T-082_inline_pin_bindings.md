# T-082 Inline pin bindings in AST->NFIR conversion

## Task summary (DoD + verify)
- Parse inline pin bindings in instance expressions and merge them into nets with `$` port rules.
- Emit conversion diagnostics for malformed bindings and endpoint overlaps.
- Update MVP AST/NFIR specs and add unit tests.
- Verify: `pytest tests/unit_tests/ir/test_converter.py -v`

## Read
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md
- src/asdl/ir/converters/ast_to_nfir.py
- tests/unit_tests/ir/test_converter.py
- docs/specs_mvp/spec_ast_mvp.md
- docs/specs_mvp/spec_asdl_nfir_mvp.md

## Plan
- [x] Add converter support for inline pin bindings and overlap diagnostics.
- [x] Add unit tests for inline bindings, overlaps, and inline-created ports.
- [x] Update MVP specs and parser hint text.
- [x] Run targeted converter tests.

## Progress log
- 2026-01-09: Understood task: parse `(pin:net ...)` groups in instance expressions, fold into nets, add ports for inline `$` nets after `nets` ports, and emit errors on malformed bindings or endpoint overlaps.
- 2026-01-09: Implemented converter changes + tests; updated MVP specs and parser note; tests passing.
- 2026-01-09: Fixed inline `$` port promotion to only occur on first inline creation and added regression test; tests passing.

## Patch summary
- Added inline pin binding parsing/merging with overlap diagnostics in `src/asdl/ir/converters/ast_to_nfir.py`.
- Added inline binding unit tests in `tests/unit_tests/ir/test_converter.py`.
- Updated MVP AST/NFIR specs for inline bindings and port order in `docs/specs_mvp/spec_ast_mvp.md` and `docs/specs_mvp/spec_asdl_nfir_mvp.md`.
- Updated instance expression hint in `src/asdl/ast/parser.py`.
- Prevented inline `$` bindings from promoting existing nets to ports and added regression coverage in `src/asdl/ir/converters/ast_to_nfir.py` and `tests/unit_tests/ir/test_converter.py`.

## PR URL
- https://github.com/Jianxun/ASDL/pull/86

## Verification
- `./venv/bin/pytest tests/unit_tests/ir/test_converter.py -v`

## Status request
- Ready for review

## Blockers / Questions
- None.

## Next steps
- Await review feedback.
