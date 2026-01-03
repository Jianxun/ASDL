# T-037 Parser Endpoint Hints

## Goal
Improve PARSE-003 diagnostics for endpoint list strings and instance expressions.

## Notes
- Endpoint lists are YAML lists only; if a string is provided, emit a clear hint to use a list of `<instance>.<pin>` strings.
- Instance expressions remain strings; keep a brief hint about `<model> key=value ...` format.

## Files
- src/asdl/ast/parser.py
- tests/unit_tests/parser/test_parser.py
