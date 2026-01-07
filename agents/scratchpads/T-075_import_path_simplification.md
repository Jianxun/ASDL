# T-075 Simplify import path resolution roots

## Task summary
- **DoD**: Update import resolution so logical paths search only CLI `--lib` roots (in order) followed by `ASDL_LIB_PATH` entries. Preserve explicit relative and absolute path handling plus env expansion. Remove project root / include-root lookups from the resolution path, and adjust ambiguity ordering to reflect the new root order. Update unit tests to match the simplified resolution behavior, including a precedence test for CLI `--lib` roots over `ASDL_LIB_PATH`.
- **Verify**: `pytest tests/unit_tests/parser -v`

## Read
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `docs/specs/spec_asdl_import.md`
- `src/asdl/imports/resolver.py`
- `tests/unit_tests/parser/test_import_resolution.py`

## Plan
1. Update resolution tests to remove project/include roots and add `--lib` precedence coverage.
2. Simplify resolver logic to only consider `lib_roots` + `ASDL_LIB_PATH` for logical paths.
3. Run parser unit tests.

## Todo
- [x] Update import resolution tests for new root order.
- [x] Simplify resolver logic and ambiguity ordering.
- [ ] Run parser unit tests.

## Progress log
- Confirmed T-075 scope: logical import paths now search only CLI `--lib` roots then `ASDL_LIB_PATH`, preserving explicit relative/absolute + env expansion.
- Updated parser import resolution tests for lib/env ordering and explicit-relative cycle fixtures.
- Simplified resolver logical root iteration to lib roots then env paths.

## Patch summary
- tests updated to remove project/include roots and assert lib/env ordering.
- resolver logical candidates now only include CLI lib roots followed by `ASDL_LIB_PATH`.

## Verification
- `./venv/bin/pytest tests/unit_tests/parser -v`

## Status request
- Done

## Blockers / Questions
- None.

## Next steps
- Reviewer: confirm import resolution ordering changes for logical paths.
