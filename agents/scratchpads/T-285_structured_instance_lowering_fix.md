# T-285 Structured Instance Lowering Fix

## Task summary (DoD + verify)
- DoD: Ensure lowering accepts both inline instance strings and structured instance objects (`ref` + optional `parameters`) through the shared parsing helper. Structured instances must not raise raw exceptions; malformed payloads must emit lowering diagnostics.
- Verify:
  - `./venv/bin/pytest tests/unit_tests/core/test_patterned_graph_lowering.py tests/unit_tests/e2e/test_pipeline_mvp.py -v`

## Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `src/asdl/lowering/ast_to_patterned_graph_instances.py`
- `src/asdl/ast/instance_expr.py`
- `tests/unit_tests/core/test_patterned_graph_lowering.py`
- `tests/unit_tests/e2e/test_pipeline_mvp.py`

## Plan
1. Add regression tests for structured instance declarations in lowering and e2e pipeline.
2. Reproduce failure to confirm raw-exception path.
3. Switch lowering instance parser usage to shared instance parsing helper.
4. Re-run task verify command and record outcomes.

## Milestone notes
- Added failing regression coverage for structured instance inputs and malformed structured payload behavior.
- Reproduced raw exception (`AttributeError`) from lowering when structured instance values flowed into inline-only parser.
- Updated lowering to call `parse_instance_value(...)` instead of inline-only parser.

## Patch summary
- `src/asdl/lowering/ast_to_patterned_graph_instances.py`
  - Normalized `_parse_instance_expr` to accept generic instance values and delegate to `parse_instance_value(..., strict_params=True)`.
- `tests/unit_tests/core/test_patterned_graph_lowering.py`
  - Added unit regression for structured instance declarations (`InstanceDecl`) and parameter lowering behavior.
- `tests/unit_tests/e2e/test_pipeline_mvp.py`
  - Added e2e regression for parsed structured instance declarations.
  - Added malformed structured payload regression (via `model_construct`) to assert diagnostics (`IR-001`) instead of exception crashes.

## PR URL
- Pending

## Verification
- Progress log:
  - `./venv/bin/pytest tests/unit_tests/core/test_patterned_graph_lowering.py tests/unit_tests/e2e/test_pipeline_mvp.py -k 'structured_instance or malformed_structured_instance' -v` -> 3 passed
  - `./venv/bin/pytest tests/unit_tests/core/test_patterned_graph_lowering.py tests/unit_tests/e2e/test_pipeline_mvp.py -v` -> 29 passed

## Status request
- In Progress

## Blockers / Questions
- None.

## Next steps
1. Push branch and open PR to `main`.
2. Update `agents/context/tasks_state.yaml` to `ready_for_review` with PR number and lint state.
