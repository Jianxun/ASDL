# T-016 Diagnostic Core

## Goal
- Implement shared diagnostic types and renderers to unblock parser diagnostics.

## Notes
- Keep schema minimal and stable (code, severity, message, spans, labels, notes, help, fix-its).
- Deterministic ordering for output and tests.
