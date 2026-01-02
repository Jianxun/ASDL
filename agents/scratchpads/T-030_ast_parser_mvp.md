# T-030 AST + Parser MVP Refactor

## Goal
Align `src/asdl/ast/` models + parser with `docs/specs_mvp/spec_ast_mvp.md` (net-first, minimal AST).

## Scope / likely files
- `src/asdl/ast/models.py`
- `src/asdl/ast/parser.py`
- `src/asdl/ast/__init__.py`
- `tests/unit_tests/parser/test_parser.py`
- `tests/unit_tests/ast/test_models.py` (new)

## Spec reminders (AST MVP)
- AsdlDocument: only `top`, `modules`, `devices`.
- ModuleDecl: only `instances` and `nets`.
- InstancesBlock/NetsBlock: ordered mapping of `str -> str` (raw instance expr / endpoint list).
- DeviceDecl: `ports` list, `params` optional, `backends` non-empty.
- DeviceBackendDecl: `template` required; backend extras are allowed as raw values.
- Hard requirements: `top` required if >1 module; at least one of `modules` or `devices` present; forbid imports/exports/views/ports fields.

## Notes
- Keep location attachment working via `_loc` on `AstBaseModel`.
- Preserve mapping order from YAML for nets/instances.
