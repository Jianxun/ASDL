# Task summary (DoD + verify)
- DoD: Add a JSON-serializable conversion for ProgramGraph plus registries (pattern expressions, origins, spans, schematic hints) and a deterministic `dump_patterned_graph` string helper. Document the JSON shape in `docs/specs_refactor/spec_refactor_patterned_graph.md` and add unit tests for a minimal graph serialization.
- Verify: `venv/bin/pytest tests/unit_tests/core/test_patterned_graph_dump.py -v`

# Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`

# Plan
- Add unit tests covering minimal PatternedGraph JSON serialization + deterministic dump output.
- Implement `patterned_graph_to_jsonable` + `dump_patterned_graph` with registry/graph coverage.
- Document JSON payload shape in the PatternedGraph refactor spec.
- Run targeted unit tests and capture results.

# Progress log
- Read context and prepared scratchpad/task state.
- Added JSON dump helpers plus unit tests for serialization coverage.
- Documented PatternedGraph JSON payload shape in refactor spec.
- Ran targeted unit tests.

# Patch summary
- Added `asdl.core.dump` with JSON serialization and deterministic dump helper.
- Exported dump helpers from `asdl.core` and added unit tests.
- Documented JSON payload shape in refactor PatternedGraph spec.

# PR URL
- TODO

# Verification
- `venv/bin/pytest tests/unit_tests/core/test_patterned_graph_dump.py -v`

# Status request (Done / Blocked / In Progress)
- In Progress

# Blockers / Questions
- None

# Next steps
- TODO
