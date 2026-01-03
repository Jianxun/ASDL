# T-039 CLI Help

## Goal
Improve `asdlc --help` so command list is visible and includes `netlist`.

## Notes
- Add a CLI test that asserts command listing output.
- Investigate why netlist is missing from top-level help (if reproducible).

## Files
- src/asdl/cli/__init__.py
- tests/unit_tests/cli/
- pyproject.toml (entrypoint verification)
