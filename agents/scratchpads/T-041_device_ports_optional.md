# T-041 Device Ports Optional

## Goal
Make `DeviceDecl.ports` optional in the AST schema so templates can omit ports entirely.

## Notes
- Update AST models and any validation that assumes ports are present.
- Confirm downstream behavior (NFIR/IFIR conversion, emission) for portless devices.

## Files
- src/asdl/ast/models.py
- tests/unit_tests/ast/
- tests/unit_tests/ir/
