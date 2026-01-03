# T-039 CLI Help

## Goal
Improve `asdlc --help` so command list is visible and includes `netlist`.

## DoD
- Improve `asdlc --help` so the top-level menu lists `netlist` and includes a brief command summary
- Add a CLI help test that asserts the command list appears

## Read
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.md
- agents/context/handoff.md
- src/asdl/cli/__init__.py
- tests/unit_tests/cli/test_netlist.py

## Current state
Checked `asdlc --help` output - netlist command IS already listed with summary:
```
Commands:
  netlist  Generate an ngspice netlist from ASDL.
```

Click is already generating the help correctly from the docstring.

## Plan
1. Add a test `test_cli_help` that verifies:
   - Help output includes "netlist" command
   - Help output includes the command summary
   - Help output has expected structure
2. Run tests to confirm coverage

## Progress log
- Set T-039 to In Progress in tasks.md
- Created feature branch feature/T-039-cli-help
- Investigated current help output - already working correctly
- Primary task is adding test coverage
- Added test_cli_help() that asserts Commands, netlist, and summary appear in help output
- Tests pass: 4 passed in 0.18s

## Patch summary
- tests/unit_tests/cli/test_netlist.py: added test_cli_help() to verify help output structure

## Verification
```
pytest tests/unit_tests/cli -v
```
Result: 4 passed in 0.18s, including new test_cli_help

## Files
- tests/unit_tests/cli/test_netlist.py (added test_cli_help)

## Next steps
- None (task complete)

## PR
- https://github.com/Jianxun/ASDL/pull/37
