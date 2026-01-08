# T-037 Parser Endpoint Hints

## Task summary
- DoD: Update PARSE-003 diagnostics after list-only endpoint authoring lands (T-043). Ensure errors explicitly say endpoint lists must be YAML lists of `<instance>.<pin>` strings; keep instance expr hints for `<model> key=value ...`. Add parser tests for the improved message/notes.
- Verify: `pytest tests/unit_tests/parser`.

## Read
- agents/context/contract.md
- agents/context/tasks.md
- agents/scratchpads/T-037_parser_endpoint_hints.md
- src/asdl/ast/parser.py
- src/asdl/ast/models.py
- tests/unit_tests/parser/test_parser.py

## Plan
- Add parser-side hinting for PARSE-003 when endpoint lists are authored as strings and when instance exprs fail validation.
- Update/add parser tests asserting the improved diagnostics.
- Run parser tests.

## Progress log
- 2026-01-02: Set T-037 to In Progress and created branch `feature/T-037-parser-endpoint-hints`.
- 2026-01-02: Added parser diagnostics notes for endpoint lists and instance expressions; updated parser tests.

## Patch summary
- `src/asdl/ast/parser.py`: add endpoint/instance hint notes and tidy endpoint validation message.
- `tests/unit_tests/parser/test_parser.py`: add hint assertions for endpoint list and instance expression diagnostics.

## PR URL
- https://github.com/Jianxun/ASDL/pull/33

## Verification
- `venv/bin/pytest tests/unit_tests/parser` (pass)

## Blockers / Questions
- 

## Next steps
- Await review on PR https://github.com/Jianxun/ASDL/pull/33.
