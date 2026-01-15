# T-131 Remove bundle usage from GraphIR converters

## Task summary (DoD + verify)
- DoD: Remove bundle/pattern_expr handling from GraphIR->IFIR and GraphIR->AST
  converters, replacing rebundling with the new pattern_origin/table approach.
  Keep converters compiling with atomized-only GraphIR.
- Verify: None listed.

## Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

## Plan
- [x] Add unit test for pattern_origin propagation via expression table.
- [x] Update GraphIR->IFIR converter to resolve pattern_origin with table entries.
- [ ] GraphIR->AST converter deferred per user override.

## Progress log
- 2026-01-xx: Task started; scratchpad initialized.
- 2026-01-xx: Added unit test covering pattern_origin propagation.
- 2026-01-xx: Updated GraphIR->IFIR converter to resolve pattern_origin from table.

## Patch summary
- Added IFIR converter unit test for pattern_origin mapping.
- Added pattern origin table lookup helper.
- Resolved GraphIR->IFIR pattern_origin using module expression table.

## PR URL
- TBD.

## Verification
- `./venv/bin/pytest tests/unit_tests/ir/test_ifir_converter.py`

## Status request
- In progress.

## Blockers / Questions
- GraphIR->AST converter update deferred per user override.

## Next steps
- Review converter code paths and implement atomized-only handling.
