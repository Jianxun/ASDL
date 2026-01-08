# T-048 Unified netlist emitter rewrite

## Task summary
- DoD: Replace ngspice-specific emitter with unified netlist emitter (new module/package). Remove `emit_ngspice` and `src/asdl/emit/ngspice.py` entirely; update `src/asdl/emit/__init__.py` and all call sites/tests. Add dedicated netlist verification pass under `src/asdl/emit/` (xDSL ModulePass) and run it before lowering/rendering. Add CLI `--backend` (default `sim.ngspice`) and drive output extension from `config/backends.yaml` per-backend `extension` key (verbatim). Update backend config schema to `extension`, `comment_prefix`, `templates`; adjust loader/tests accordingly. Ensure top module emits no wrapper when `top_as_subckt` is false. Update specs and rebaseline netlist tests to new backend naming.
- Verify: `pytest tests/unit_tests/emit -v && pytest tests/unit_tests/netlist -v && pytest tests/unit_tests/cli -v && pytest tests/unit_tests/e2e -v`

## Read
- `agents/roles/executor.md`
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.md`
- `agents/context/handoff.md`

## Plan
1. Inspect current emit/CLI pipeline and backend config loader to identify ngspice-specific surfaces to replace.
2. Implement unified netlist emitter module + verification pass; update CLI backend selection and output extension logic.
3. Update backend config schema and tests, rebaseline netlist tests/specs, then run verify commands.

## Progress log
- 2026-01-03: Set task T-048 to In Progress; created scratchpad structure.

## Patch summary
- None yet.

## PR URL
- https://github.com/Jianxun/ASDL/pull/41

## Verification
- Not run yet.

## Blockers / Questions
- None yet.

## Next steps
1. Inspect current emission/CLI code paths for ngspice-specific entry points and backend config schema.
