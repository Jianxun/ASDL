# T-128 Remove IFIR pattern passes

## Task summary (DoD + verify)
- DoD: Delete IFIR atomization/elaboration passes and update the patterns package and
  pipeline to remove the atomize-patterns pass.
- Verify: None.

## Read
- agents/context/tasks.yaml
- agents/scratchpads/T-128_remove_ifir_pattern_passes.md
- src/asdl/ir/patterns/atomization.py
- src/asdl/ir/patterns/elaboration.py
- src/asdl/ir/patterns/__init__.py
- src/asdl/ir/pipeline.py

## Plan
- Remove IFIR pattern pass implementations.
- Update patterns package exports.
- Remove atomize-patterns wiring from the pipeline.

## Progress log
- Removed IFIR atomization/elaboration pass implementations and exports.
- Dropped atomize-patterns from the pipeline.
- Removed obsolete IFIR pattern atomization tests after pass deletion.

## Patch summary
- Deleted IFIR pattern pass modules.
- Simplified patterns package exports.
- Removed atomize-patterns pipeline pass.
- Deleted obsolete IFIR atomization unit test.

## PR URL
- https://github.com/Jianxun/ASDL/pull/136

## Verification
- Not run (not requested).

## Status request
- ready_for_review

## Blockers / Questions
- None.

## Next steps
- Run tests if desired.
