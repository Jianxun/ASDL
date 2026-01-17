# Diagnostics E2E Cases

This folder holds end-to-end diagnostic fixtures driven by a manifest. Each
case captures a single diagnostic code and the exact CLI invocation needed
to surface it.

## Layout
- `tests/e2e/diagnostics/manifest.yaml`: case catalog for pytest.
- `tests/e2e/diagnostics/<CODE>_<slug>/`: one directory per diagnostic case.
  - `case.asdl`: minimal input that triggers the diagnostic.
  - `README.md`: short description and the exact `asdlc` command.
  - `expected.txt`: expected stderr output for the command.

## Naming
- Case directories use `<CODE>_<slug>` where `<CODE>` is the diagnostic code
  (for example, `PARSE-001`) and `<slug>` is a short lowercase description
  using underscores.

## Command conventions
- Default command is `asdlc netlist case.asdl`.
- Use `asdlc ir-dump --ir graphir|ifir case.asdl` when the diagnostic is
  specific to IR lowering or verification.
- Use `asdlc schema ...` for CLI schema diagnostics that are not tied to
  netlist emission.

## Manifest format
`manifest.yaml` is the source of truth for pytest. Top-level keys are
`schema_version` and `cases`. Each case entry includes:
- `code`: diagnostic code (must match the spec).
- `case_dir`: directory name for the case (relative to this folder).
- `args`: CLI arguments passed to `asdlc` (run from within `case_dir`).
- `expected_exit`: integer exit code expected from the command.
- `env`: optional map of environment overrides for the command.
- `status`: one of `pending`, `ready`, or `needs-harness` (pytest only runs
  `ready` cases).

## Pytest harness expectations
- The harness is manifest-driven and runs `asdlc` for each `ready` entry.
- It asserts the process exit code and compares stderr to `expected.txt`.
- Only trailing newline differences are normalized; keep `expected.txt`
  byte-for-byte with the rendered diagnostics.
