# T-018 Linter

## Goal
- Define lint rule registry and configuration to run rule-only diagnostics.

## Notes
- Rules emit shared diagnostics; config overrides severities/enabled state.
- CLI surface: `asdl lint` and `--max-warnings`.
