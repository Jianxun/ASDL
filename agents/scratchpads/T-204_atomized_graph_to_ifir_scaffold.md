# T-204 AtomizedGraph -> IFIR lowering scaffold and happy path

## Task summary (DoD + verify)
- Implement AtomizedGraph -> IFIR lowering under `src/asdl/lowering/atomized_graph_to_ifir.py` with a happy-path conversion that builds IFIR design, modules, nets, instances, and devices.
- Export the entry point in lowering `__init__` and add a unit test for the happy-path conversion.
- Verify with `venv/bin/pytest tests/unit_tests/lowering/test_atomized_graph_to_ifir.py -v`.

## Read
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`

## Plan
- [x] Define AtomizedGraph -> IFIR conversion API and diagnostics.
- [x] Implement happy-path lowering to IFIR ops and wire into lowering `__init__`.
- [ ] Add happy-path unit test and run verify.

## Progress log
- 2026-01-23 20:23 — Task intake, read context, created scratchpad; next step set task status in progress and implement lowering.
- 2026-01-23 20:27 — Set T-204 to in_progress, created lowering scaffold and IFIR conversion, wired export; next step add tests and verify.

## Patch summary
- Pending.

## PR URL
- Pending.

## Verification
- Pending.

## Status request
- In progress.

## Blockers / Questions
- None yet.

## Next steps
- Implement conversion scaffolding and happy-path test.
