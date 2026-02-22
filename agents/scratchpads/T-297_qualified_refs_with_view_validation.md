# T-297 - Restore import-qualified instance refs with decorated-symbol validation

## Goal
Allow valid import-qualified refs (`ns.symbol`) while preserving decorated symbol validation semantics.

## Scope
- Accept `ns.symbol` and `ns.symbol@view` where symbol token passes module-symbol grammar.
- Keep module declaration-name grammar strict (`cell` or `cell@view`).
- Preserve clear parser diagnostics for malformed decorated forms.

## Verify
- `./venv/bin/pytest tests/unit_tests/ast/test_models.py tests/unit_tests/parser/test_parser.py tests/unit_tests/cli/test_netlist.py -k "imports_with or malformed_decorated or module_symbol" -v`
