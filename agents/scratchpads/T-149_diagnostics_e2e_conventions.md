# T-149 Diagnostics e2e conventions and manifest

## Task summary (DoD + verify)
- DoD: Create `tests/e2e/diagnostics/README.md` documenting the directory layout, naming (`<CODE>_<slug>`), required files per case (`case.asdl`, `README.md`, `expected.txt`), and command conventions (default to `asdlc netlist`, use `ir-dump`/`schema` when required). Document the pytest harness expectations (manifest-driven, `expected.txt` compares stderr) and required manifest fields (case directory, CLI args, expected exit, optional env, and `status` enum like `pending`/`ready`/`needs-harness` used by pytest selection). Add `tests/e2e/diagnostics/manifest.yaml` enumerating every diagnostic code from `docs/specs/spec_diagnostic_codes.md`.
- Verify: `rg -n "PARSE-001" tests/e2e/diagnostics/manifest.yaml`

## Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `docs/specs/spec_diagnostic_codes.md`

## Plan
Todo:
- [x] Draft diagnostics e2e README with layout, naming, manifest, and command conventions.
- [x] Create diagnostics manifest enumerating all spec diagnostic codes with required fields.
- [x] Run verify command and update status.

## Progress log
- 2026-01-xx: Initialized scratchpad and drafted README/manifest scaffolding.
- 2026-01-xx: Ran manifest verification and opened PR #158.

## Patch summary
- Added diagnostics e2e README conventions.
- Added manifest enumerating all diagnostic codes with default metadata.

## PR URL
- https://github.com/Jianxun/ASDL/pull/158

## Verification
- `rg -n "PARSE-001" tests/e2e/diagnostics/manifest.yaml`

## Status request
- Ready for Review

## Blockers / Questions
- None.

## Next steps
- None.
