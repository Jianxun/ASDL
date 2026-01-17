# Task summary (DoD + verify)
- DoD: Ensure GraphIR verification errors for duplicate endpoints report the instance name (not the internal inst_id) and propagate a source span when available. Store endpoint source locations in GraphIR ops, and have GraphIR verification/pipeline diagnostics surface spans for duplicate endpoint errors. Add unit tests that assert the diagnostic message uses the instance name and includes a primary span.
- Verify: `venv/bin/pytest tests/unit_tests/ir/test_graphir_structure.py -v`

# Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`

# Plan
- Identify duplicate endpoint verification path and how diagnostics are built.
- Capture endpoint source spans in GraphIR ops during AST->GraphIR lowering.
- Ensure diagnostics use instance name and attach endpoint span.
- Add/adjust unit tests for message text and primary span.

# Progress log
- Added unit test covering duplicate endpoint diagnostics span/name expectations.
- Captured endpoint source annotations and plumbed span-aware GraphIR verification diagnostics.

# Patch summary
- `EndpointOp` now accepts annotations and endpoint lowering attaches source locations.
- GraphIR module verification reports duplicate endpoints with instance names and span-aware diagnostics.
- Added diagnostic coverage for duplicate endpoint message/span expectations.

# PR URL
- https://github.com/Jianxun/ASDL/pull/160

# Verification
- `venv/bin/pytest tests/unit_tests/ir/test_graphir_structure.py -v`

# Status request (Done / Blocked / In Progress)
- Done

# Blockers / Questions
- 

# Next steps
- Await review.
