# T-298 - Support occurrence-specific view application for reused module definitions

## Goal
Support path-scoped divergent bindings when a module definition is instantiated multiple times.

## Scope
- Remove current non-uniform rewrite failure in view-apply flow.
- Ensure emission honors per-occurrence resolved refs deterministically.
- Preserve sidecar ordering and resolver semantics.

## Verify
- `./venv/bin/pytest tests/unit_tests/views/test_view_apply.py tests/unit_tests/cli/test_netlist.py -k "view_fixture_binding_profiles_change_emitted_instance_refs or non_uniform or scoped_override" -v`
