# T-128 Remove IFIR pattern passes

## Objective
- Delete IFIR atomization/elaboration passes and remove pipeline wiring.

## Notes
- Pipeline should compile without atomize-patterns pass.

## Files
- src/asdl/ir/patterns/atomization.py
- src/asdl/ir/patterns/elaboration.py
- src/asdl/ir/patterns/__init__.py
- src/asdl/ir/pipeline.py
