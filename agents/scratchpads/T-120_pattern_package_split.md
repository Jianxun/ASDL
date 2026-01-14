# Task summary
- DoD: Replace monolithic patterns module with `src/asdl/patterns/` package that separates tokenization, expansion, atomization, and diagnostics while preserving public API (`expand_pattern`, `expand_endpoint`, `atomize_pattern`, `atomize_endpoint`) and existing behavior. Update imports and keep diagnostics codes unchanged.
- Verify: `venv/bin/pytest tests/unit_tests/parser/test_pattern_expansion.py tests/unit_tests/parser/test_pattern_atomization.py -v`

# Read
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

# Plan
- [x] Inspect existing pattern implementation and tests to map responsibilities.
- [x] Convert `patterns.py` into package shell (`patterns/__init__.py`) with preserved API.
- [x] Split tokenization, expansion, atomization, diagnostics into separate modules.
- [x] Update imports and ensure tests pass.

# Progress log
- 2026-02-08: Read task context and current pattern implementation/tests.
- 2026-02-08: Converted `src/asdl/patterns.py` into package `src/asdl/patterns/__init__.py`.
- 2026-02-08: Split patterns package into diagnostics, tokenize, expand, atomize modules.
- 2026-02-08: Verified parser pattern expansion/atomization tests.

# Patch summary
- Converted `asdl.patterns` into a package with dedicated diagnostics/tokenize/expand/atomize modules.
- Re-exported public API from `src/asdl/patterns/__init__.py` with docstrings preserved.

# PR URL
- https://github.com/Jianxun/ASDL/pull/129

# Verification
- `venv/bin/pytest tests/unit_tests/parser/test_pattern_expansion.py tests/unit_tests/parser/test_pattern_atomization.py -v`

# Status request
- Ready for Review

# Blockers / Questions
- 

# Next steps
- 
