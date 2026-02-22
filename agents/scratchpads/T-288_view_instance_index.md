# T-288 — Add deterministic hierarchical instance index for view binding

## Task summary (DoD + verify)
- DoD: Build a deterministic hierarchical instance index for binding resolution. Index entries must include parent path (excluding leaf instance name), instance leaf name, and referenced logical module symbol context needed by resolver predicates. Match semantics must support missing `path` as root-level scope.
- Verify:
  - `./venv/bin/pytest tests/unit_tests/views/test_instance_index.py -v`

## Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `docs/specs/spec_asdl_view_config.md`
- `agents/adr/ADR-0033-view-binding-config-and-sidecar.md`

## Plan
- Add unit tests for deterministic hierarchical instance indexing and scope matching semantics.
- Implement index model + builder APIs in `src/asdl/views/instance_index.py`.
- Wire public exports and any shared models updates in `src/asdl/views/models.py` and `src/asdl/views/__init__.py`.
- Run focused verification and record results.

## Milestone notes
- Intake complete.
- Added failing unit tests first for hierarchical traversal order, root-scope matching, subtree path matching, and decorated module normalization.
- Implemented deterministic preorder hierarchical index builder and path/match helpers.
- Exported index APIs from `asdl.views` and verified focused views test coverage passes.

## Patch summary
- Added `src/asdl/views/instance_index.py` with:
  - `ViewInstanceIndexEntry` entries containing `path`, `instance`, logical `module`, authored `ref`, and `ref_file_id`.
  - `build_instance_index(design)` for deterministic preorder DFS traversal from the resolved top module.
  - `match_index_entries(index, match)` implementing scope semantics:
    - missing `path` => root-level scope (`path == ""`)
    - provided `path` => subtree scope (`full_path == path` or descendant)
  - module symbol normalization helper (`cell@view` -> logical `cell`) for module predicate matching.
- Updated `src/asdl/views/__init__.py` to export instance index APIs.
- Added `tests/unit_tests/views/test_instance_index.py` covering deterministic ordering, root-scope behavior, subtree scoping, and decorated symbol normalization.

## PR URL
- Pending PR creation.

## Verification
- `./venv/bin/pytest tests/unit_tests/views/test_instance_index.py -v` (pass; 4 passed)
- `./venv/bin/pytest tests/unit_tests/views/test_view_config.py tests/unit_tests/views/test_instance_index.py -v` (pass; 9 passed)

## Status request (Done / Blocked / In Progress)
- In Progress (ready to open PR and request review)

## Blockers / Questions
- None.

## Next steps
- Implement TDD cycle for instance index and verify.
