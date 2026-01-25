# T-223 Move legacy xDSL specs under docs/legacy

## Task summary (DoD + verify)
- Relocate legacy GraphIR/IFIR/NFIR specs and xDSL-era pipeline docs from `docs/specs/` into `docs/legacy/`.
- Add a brief README in `docs/legacy/` describing decommissioned status.
- Update any in-repo references to point to the new paths.
- Verify: `venv/bin/pytest tests/unit_tests/cli -v`.

## Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

## Plan
- Inspect docs/specs for legacy xDSL-era docs and current references.
- Move identified legacy specs into docs/legacy and add README.
- Update codebase map and any doc references to new paths.
- Run verify command or document skip reason.

## Todo
- [ ] Move legacy specs into `docs/legacy` and add README.
- [ ] Update references (docs/codebase_map) to new paths.
- [ ] Run verify command or document skip.

## Progress log

## Patch summary

## PR URL

## Verification

## Status request

## Blockers / Questions

## Next steps
- 2026-01-25 01:23 — Task intake; read contract/tasks/status; created scratchpad; set T-223 in_progress; created feature branch; next step inspect docs/specs and references.
