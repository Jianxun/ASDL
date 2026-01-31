# T-244 Sphinx domain

## Task summary (DoD + verify)
- DoD: Implement a minimal Sphinx domain that registers ASDL objects (doc, module, port, net, inst, var, pattern, import) with reference roles matching the agreed naming scheme. Provide registration entry points and stable target IDs without requiring Sphinx directives to parse ASDL files yet. Include minimal unit coverage for object registration and target naming. Do not touch unrelated style docs (e.g., docs/code_styles/docstrings_comments.md).
- Verify: ./venv/bin/pytest tests/unit_tests/docs/test_sphinx_domain.py -v

## Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

## Plan
- Identify existing docs tooling and patterns for domains in codebase.
- Define minimal domain API with roles/object types and stable target ID helpers.
- Add unit tests for registration + target naming.
- Run verify command.
### Todo
- [x] Define Sphinx domain helpers + registry/target ID utilities.
- [x] Update docs package exports.
- [x] Add unit tests for target IDs + registration.
- [x] Run verify command.

## Progress log
- 2026-01-31 00:00 — Task intake; confirmed T-244 in tasks.yaml/state; read contract/lessons/project_status; next step implement domain + tests.
- 2026-01-31 00:00 — Drafted Sphinx domain helpers with stable target ids and registry; added exports in docs __init__; next step add unit tests.
- 2026-01-31 00:00 — Added unit tests for target naming and registration; next step run verify.
- 2026-01-31 00:00 — Ran pytest for docs domain tests; all passed; next step commit changes.
- 2026-01-31 00:00 — Committed Sphinx domain helpers (c08fd7e); next step commit tests + task state.
- 2026-01-31 00:00 — Committed unit tests and task tracking updates (c87ea62); next step update scratchpad and closeout.
- 2026-01-31 00:00 — Opened PR https://github.com/Jianxun/ASDL/pull/258; next step update task state.
- 2026-01-31 00:00 — Set T-244 ready_for_review and committed task state (755fae9); next step finalize scratchpad.
- 2026-01-31 00:35 — Review intake: PR 258 targets main, scratchpad/verify info present; set T-244 review_in_progress and ran lint_tasks_state.py; next step scope/code review.
- 2026-01-31 00:35 — Scope review complete: changes align with T-244 DoD; no links.spec present; next step implementation review.
- 2026-01-31 00:35 — Implementation review complete: no blockers found; next step post PR comment and mark review_clean.
- 2026-01-31 00:36 — Posted review comment and set T-244 review_clean; ran lint_tasks_state.py; next step merge and closeout.
- 2026-01-31 00:36 — Set T-244 done (merged true) and ran lint_tasks_state.py; next step merge PR and clean branches.

## Patch summary
- Added ASDL Sphinx domain module with target id helpers, registry, and minimal directives.
- Exported domain helpers from the docs package.
- Added unit tests for target naming and object registration.

## PR URL
- https://github.com/Jianxun/ASDL/pull/258

## Verification
- ./venv/bin/pytest tests/unit_tests/docs/test_sphinx_domain.py -v

## Status request
- Ready for review.

## Blockers / Questions

## Next steps
