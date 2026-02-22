# T-289 — Implement view binding resolver and resolved sidecar entries

## Task summary (DoD + verify)
- Implement resolver logic that applies baseline `view_order` selection, then ordered rule overrides with later-rule precedence.
- Resolver must support `path`/`instance`/`module` predicates per spec.
- Emit sidecar entries containing `path`, `instance`, `resolved`, and `rule_id`.
- `resolved` must use full module symbol form (`cell` or `cell@view`).
- Verify: `./venv/bin/pytest tests/unit_tests/views/test_view_resolver.py -v`

## Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

## Plan
1. Inspect existing views models/index/config and spec requirements.
2. Add failing resolver tests for baseline selection, rule overrides, predicates, and sidecar shape.
3. Implement resolver logic and any minimal model/index updates required.
4. Run task verify command and record results.
5. Update task status and prepare PR handoff.

## Milestone notes
- Intake complete.
- Added failing resolver unit tests first for baseline selection, ordered
  override precedence, sidecar `rule_id` behavior, and missing-symbol failures.
- Implemented deterministic resolver with baseline + ordered rule overrides and
  sidecar entries (`path`, `instance`, `resolved`, `rule_id`) in index order.
- Exported resolver APIs from `asdl.views` and validated focused + full views
  test coverage.
- Reviewer follow-up: added strict validation that each rule `match.path`
  resolves to an existing hierarchy node and now fail fast on unknown paths.
- Added resolver regression coverage for unknown `match.path` behavior.

## Patch summary
- Added `tests/unit_tests/views/test_view_resolver.py`:
  - baseline resolution via `view_order` (including authored decorated refs)
  - later-rule precedence behavior
  - deterministic default `rule<k>` ID propagation into sidecar
  - baseline and rule-bind missing-symbol error behavior
  - unknown `match.path` now raises a resolver error
- Added `src/asdl/views/resolver.py`:
  - `ResolvedViewBindingEntry` sidecar dataclass
  - `resolve_view_bindings(design, profile)` implementing:
    - baseline selection from `view_order`
    - ordered rule overrides with later-rule precedence
    - strict `match.path` hierarchy-node validation before rule application
    - final resolved-symbol existence checks
- Updated `src/asdl/views/__init__.py` exports:
  - `ResolvedViewBindingEntry`
  - `resolve_view_bindings`

## PR URL
- Pending PR creation.

## Verification
- `./venv/bin/pytest tests/unit_tests/views/test_view_resolver.py -v` (pass, 5 passed)
- `./venv/bin/pytest tests/unit_tests/views/test_view_config.py tests/unit_tests/views/test_instance_index.py tests/unit_tests/views/test_view_resolver.py -v` (pass, 13 passed)
- `./venv/bin/pytest tests/unit_tests/views/test_view_config.py tests/unit_tests/views/test_instance_index.py tests/unit_tests/views/test_view_resolver.py -v` (pass, 14 passed)

## Status request
- Ready for Review

## Blockers / Questions
- None.

## Next steps
- Open PR and update task state to `ready_for_review` with PR number.
