# T-078 Propagate per-entry source spans into NFIR/IFIR

## Task summary (DoD + verify)
- Capture YAML locations for `nets` and `instances` map entries during parsing and store them as ModuleDecl private metadata. Use these locations to set `src` on NFIR NetOp/InstanceOp and carry them through NFIR->IFIR so downstream diagnostics resolve to file/line/col. Update IR diagnostics tests so errors tied to net/instance data include non-null spans.
- Verify: `pytest tests/unit_tests/ir -v`

## Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`

## Plan
- Capture net/instance entry spans in AST parsing and persist on ModuleDecl metadata.
- Thread spans into NFIR NetOp/InstanceOp src fields and carry to IFIR.
- Update IR diagnostics tests to assert spans are present where required.
- Run required verification and record results.

## Todo
- [x] Capture per-entry spans for nets/instances in parser + ModuleDecl metadata.
- [x] Use metadata to set NFIR NetOp/InstanceOp src and carry to IFIR.
- [x] Update IR diagnostics tests for non-null spans tied to net/instance data.
- [x] Run `pytest tests/unit_tests/ir -v`.

## Progress log
- 2026-01-10: Initialized task, captured task context.
- 2026-01-10: Stored per-entry net/instance locations on ModuleDecl and threaded src to NFIR ops.
- 2026-01-10: Updated IR diagnostics tests to assert entry spans and ran unit tests.
- 2026-01-10: Opened PR #81 and set task status to ready for review.

## Patch summary
- Added ModuleDecl private maps for net/instance entry locations, captured during parsing, and used to set net/instance src plus diagnostics in AST->NFIR.
- Updated IR converter tests to parse YAML and assert primary spans on net/instance errors.

## PR URL
- https://github.com/Jianxun/ASDL/pull/81

## Verification
- `./venv/bin/pytest tests/unit_tests/ir -v`

## Status request
- Done.

## Blockers / Questions
- None.

## Next steps
- Await review feedback.
