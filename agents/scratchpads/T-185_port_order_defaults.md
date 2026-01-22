# Task summary (DoD + verify)
- DoD: Extend PatternedGraph lowering to include `$` nets introduced by `instance_defaults` in `module_graph.port_order`, appended after explicit `$` nets from `nets`. Add coverage for port order when defaults introduce new `$` nets.
- Verify: `venv/bin/pytest tests/unit_tests/core/test_patterned_graph_lowering.py -v`

# Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`

# Plan
- Add a unit test covering port order when instance_defaults introduce new `$` nets.
- Update PatternedGraph lowering to append default-introduced ports after explicit nets.
- Run the specified pytest command and record results.

# Progress log
- Added unit coverage for port order with instance_defaults.
- Appended default-derived ports after explicit nets in PatternedGraph lowering.
- Ran pytest for patterned graph lowering tests.

# Patch summary
- `src/asdl/core/build_patterned_graph.py`: append `$` nets from instance_defaults to port_order after explicit nets.
- `tests/unit_tests/core/test_patterned_graph_lowering.py`: cover port order when defaults add new ports.

# PR URL
- https://github.com/Jianxun/ASDL/pull/190

# Verification
- `venv/bin/pytest tests/unit_tests/core/test_patterned_graph_lowering.py -v`

# Status request (Done / Blocked / In Progress)
- Ready for Review

# Blockers / Questions
- 

# Next steps
- Await reviewer feedback.
