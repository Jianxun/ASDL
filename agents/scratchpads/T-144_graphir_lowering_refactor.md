# T-144 GraphIR lowering refactor

## Task summary (DoD + verify)
- DoD: Split `lower_module` responsibilities into focused helpers (instances, nets/endpoints, and module assembly) without changing behavior or diagnostics. Keep `ast_to_graphir_lowering.py` as orchestration only and add docstrings for the new helpers. Ensure existing converter tests pass unchanged.
- Verify: `venv/bin/pytest tests/unit_tests/ir/test_graphir_converter.py -v`

## Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md
- src/asdl/ir/converters/ast_to_graphir_lowering.py
- src/asdl/ir/converters/ast_to_graphir.py
- src/asdl/ir/converters/ast_to_graphir_utils.py
- tests/unit_tests/ir/test_graphir_converter.py

## Plan
- Extract instance lowering into a helper module and wire lower_module to call it.
- Extract net/endpoint lowering into a helper module and keep port/pattern behavior intact.
- Assemble ModuleOp via a dedicated helper and verify tests.

## Progress log
- Created scratchpad and set T-144 status to in_progress.
- Extracted instance and net lowering helpers and updated module orchestration.

## Patch summary
- 

## PR URL
- 

## Verification
- 

## Status request (Done / Blocked / In Progress)
- In Progress

## Blockers / Questions
- 

## Next steps
- 
