# T-319 — Deduplicate query and netlist view-resolution orchestration

## Task summary (DoD + verify)
- DoD: Audit shared query/netlist CLI flow for view option validation and resolve+apply view-binding orchestration, then extract reusable runtime helper(s) under `src/asdl/cli/` and migrate both `asdl.cli.query_runtime.build_query_runtime` and `asdl.cli.netlist` command flow to use them. Preserve diagnostics and exit-code behavior. Document what orchestration was reused vs isolated in the scratchpad.
- Verify:
  - `./venv/bin/pytest tests/unit_tests/cli/test_query_cli_runtime.py tests/unit_tests/cli/test_netlist.py -v`

## Read (paths)
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `docs/specs/spec_cli_query.md`
- `agents/adr/ADR-0037-cli-query-semantics.md`

## Plan
- [ ] Perform reuse audit across query and netlist CLI orchestration.
- [ ] Extract shared runtime/view-resolution helper(s) under `src/asdl/cli/`.
- [ ] Migrate query and netlist command flows to shared helper(s).
- [ ] Add/update tests proving diagnostics/exit-code parity.
- [ ] Run verify command and summarize reused vs isolated functionality.

