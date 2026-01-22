# Task summary (DoD + verify)
- DoD: Update PatternedGraph lowering diagnostics to use existing IR codes (IR-001/IR-002/IR-003 where applicable) per `docs/specs/spec_diagnostic_codes.md`. Add tests asserting the emitted codes for invalid instance/endpoint and pattern parse failures.
- Verify: `venv/bin/pytest tests/unit_tests/core/test_patterned_graph_lowering.py -v`

# Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`

# Plan
- Add tests covering diagnostic codes for invalid instance/endpoint references and pattern parse failures.
- Update PatternedGraph lowering diagnostics to emit IR-001/IR-002/IR-003 codes per spec.
- Run the specified pytest command and record results.

# Progress log
- Added unit tests for invalid instance/endpoint and pattern parse diagnostic codes.
- Aligned PatternedGraph diagnostic codes with IR-001/IR-002/IR-003.
- Ran patterned graph lowering tests.

# Patch summary
- `tests/unit_tests/core/test_patterned_graph_lowering.py`: assert IR codes for instance/endpoint/pattern parse failures.
- `src/asdl/core/build_patterned_graph.py`: map diagnostics to IR-001/IR-002/IR-003.

# PR URL
- 

# Verification
- `venv/bin/pytest tests/unit_tests/core/test_patterned_graph_lowering.py -v`

# Status request (Done / Blocked / In Progress)
- In Progress

# Blockers / Questions
- 

# Next steps
- Open PR and request review.
