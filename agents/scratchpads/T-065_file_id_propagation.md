# Task summary (DoD + verify)
- DoD: Carry `file_id` metadata from import resolution through NFIR/IFIR: add `entry_file_id` on design ops, `file_id` on module/device ops, and `ref_file_id` on instance ops. Update AST->NFIR and NFIR->IFIR converters to set/copy these attributes from the import ProgramDB/NameEnv. Adjust IR verification to allow same-name modules/devices across files (uniqueness per `file_id`) while still enforcing same-file uniqueness. Ensure `top` resolves within the entry file only (via `entry_file_id`). Add IR tests covering duplicate names across files and entry-top resolution.
- Verify: `pytest tests/unit_tests/ir -v`

# Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`

# Plan
- Add IR tests for file_id propagation + entry-file top resolution/duplicate handling.
- Update NFIR/IFIR dialects + converters + pattern elaboration to carry file_id metadata.
- Adjust IR verification for per-file uniqueness and entry-file top checks.
- Run `pytest tests/unit_tests/ir -v` and record results.

## Todo
- [x] Add converter tests for entry_file_id/file_id/ref_file_id propagation.
- [x] Add dialect verification tests for cross-file duplicates + entry top resolution.
- [x] Implement dialect/converter/pattern elaboration updates.
- [x] Run IR unit tests and capture output.

# Progress log
- Added file_id/entry_file_id/ref_file_id attributes to NFIR/IFIR ops and propagated through converters/pattern elaboration.
- Added IR tests for file_id propagation and entry-file top resolution + per-file uniqueness.
- Ran IR unit tests.

# Patch summary
- Added file_id metadata attributes and propagation across NFIR/IFIR and pattern elaboration.
- Updated IR dialect verification to scope uniqueness per file and enforce entry-file top resolution.
- Added unit tests for propagation and verification behaviors.

# Verification
- `./venv/bin/pytest tests/unit_tests/ir -v`

# Status request (Done / Blocked / In Progress)
- Done

# Blockers / Questions
- None.

# Next steps
- Await review feedback.

## PR URL
- https://github.com/Jianxun/ASDL/pull/72

