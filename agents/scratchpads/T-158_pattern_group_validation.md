# Task summary (DoD + verify)
- DoD: Update AST pattern group validation to accept only `<...>` group tokens, update pattern tokenization to parse numeric ranges inside `<...>`, reject legacy `[]` ranges or mixed `|`/`:` groups, and refresh parser unit tests to use `<start:end>` syntax with updated expected strings.
- Verify: `venv/bin/pytest tests/unit_tests/parser/test_pattern_atomization.py tests/unit_tests/parser/test_pattern_expansion.py tests/unit_tests/parser/test_parser.py -v`

# Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`

# Plan
- [ ] Inspect pattern group validation and tokenizer handling for range groups.
- [ ] Update validation/tokenization for `<start:end>` only and add error coverage.
- [ ] Refresh parser unit tests for `<start:end>` expected strings.
- [ ] Run targeted parser tests.
- [ ] Open PR and finalize task status.

# Progress log
- 2026-01-19: Initialized scratchpad and set task to in progress.

# Patch summary
- 

# PR URL
- 

# Verification
- 

# Status request (Done / Blocked / In Progress)
- In Progress

# Blockers / Questions
- None.

# Next steps
- Inspect current validation/tokenization behavior and adjust for `<start:end>` ranges.
