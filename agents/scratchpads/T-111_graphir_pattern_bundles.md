# T-111 GraphIR pattern bundles

## Task summary (DoD + verify)
- DoD: Wire pattern expansion metadata into GraphIR bundles/pattern_expr ops, implement rebundling rules, and ensure projections honor bundle ordering without pattern inference. Add targeted pattern unit tests.
- Verify: venv/bin/pytest tests/unit_tests/ir/test_pattern_atomization.py -v

## Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

## Plan
- Review GraphIR pattern spec + existing bundle ops to align metadata needs.
- Add bundle metadata wiring and rebundling helpers for ordered projections.
- Add rebundling unit coverage for bundle ordering + eligibility splits.

## Progress log
- Read GraphIR pattern spec and current GraphIR ops/converters.
- Added bundle metadata support + rebundling helpers and wrappers.
- Added rebundling tests and ran the target pytest command.

## Patch summary
- Add bundle metadata keys/validation in `BundleOp` and rebundling utilities.
- Introduce GraphIR rebundling helpers and wrapper APIs in atomization/elaboration.
- Add rebundling tests for order, gaps, eligibility splits, and missing metadata.

## PR URL
- https://github.com/Jianxun/ASDL/pull/124

## Verification
- `venv/bin/pytest tests/unit_tests/ir/test_pattern_atomization.py -v`

## Status request (Done / Blocked / In Progress)
- Done

## Blockers / Questions
- 

## Next steps
- 
