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
- [ ] Run verify command and update status.

## Progress log
- 2026-01-xx: Initialized scratchpad and drafted README/manifest scaffolding.

## Patch summary
- TBD

## PR URL
- TBD

## Verification
- TBD

## Status request
- TBD

## Blockers / Questions
- None.

## Next steps
- TBD
