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

## Patch summary

## PR URL

## Verification

## Status request

## Blockers / Questions

## Next steps

- 2026-01-31 00:00 — Task intake; confirmed T-244 in tasks.yaml/state; read contract/lessons/project_status; next step implement domain + tests.
- 2026-01-31 00:00 — Drafted Sphinx domain helpers with stable target ids and registry; added exports in docs __init__; next step add unit tests.
- 2026-01-31 00:00 — Added unit tests for target naming and registration; next step run verify.
- 2026-01-31 00:00 — Ran pytest for docs domain tests; all passed; next step commit changes.
- 2026-01-31 00:00 — Committed Sphinx domain helpers (c08fd7e); next step commit tests + task state.
- 2026-01-31 00:00 — Committed unit tests and task tracking updates (c87ea62); next step update scratchpad and closeout.
