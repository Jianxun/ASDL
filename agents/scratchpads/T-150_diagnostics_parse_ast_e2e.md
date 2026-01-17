# T-150 PARSE and AST diagnostics e2e cases

## Task summary (DoD + verify)
- DoD: Add case directories for PARSE-001..004 and AST-010..022 under `tests/e2e/diagnostics/` following the conventions. Each case includes a standalone `case.asdl`, a short `README.md` with the exact `asdlc` command, and `expected.txt` capturing stderr diagnostics. Update `manifest.yaml` entries with the command, exit code, status (`ready` or `needs-harness`), and any notes about spans or multi-file import fixtures.
- Verify: `./venv/bin/asdlc netlist tests/e2e/diagnostics/PARSE-001_yaml_parse_error/case.asdl`

## Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `tests/e2e/diagnostics/README.md`
- `tests/e2e/diagnostics/manifest.yaml`
- `docs/specs/spec_diagnostic_codes.md`
- `src/asdl/ast/parser.py`
- `src/asdl/imports/diagnostics.py`
- `src/asdl/ast/named_patterns.py`

## Plan
Todo:
- [x] Build PARSE-001..004 case directories with inputs and expected stderr.
- [ ] Build AST-010..022 case directories + fixtures and expected stderr.
- [ ] Update diagnostics manifest entries with args/status/notes.
- [ ] Run verify command and record results.

## Progress log
- 2026-01-xx: Initialized scratchpad and added PARSE-001..004 fixtures with expected stderr.

## Patch summary
- TBD

## PR URL
- TBD

## Verification
- TBD

## Status request
- In Progress

## Blockers / Questions
- None.

## Next steps
- TBD
