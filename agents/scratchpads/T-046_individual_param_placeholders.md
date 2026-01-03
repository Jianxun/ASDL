# T-046 Individual Parameter Placeholders

## Task summary
- DoD: Expose individual merged parameter values as template placeholders in the ngspice emitter. After merging device/backend/instance params, add each key-value pair from the merged dict to `template_values` (not just the formatted `params_str`). This allows templates to reference individual params like `{L}`, `{W}`, `{NF}`, `{m}`. Preserve backward compat with `{params}` placeholder for the formatted string. Add tests for templates using individual param placeholders.
- Verify: `pytest tests/unit_tests/netlist`.

## Root cause analysis
Before this fix, the `_merge_params` function created a merged dictionary of device/backend/instance parameters but only returned the formatted string (e.g., `"L=0.2u W=5u NF=2 m=1"`). Individual parameter values were not accessible as template placeholders.

Templates that tried to use `{L}`, `{W}`, etc. would fail with `EMIT-003: Backend template references unknown placeholder 'L'`.

## Implementation
Modified `src/asdl/emit/ngspice.py`:

1. Updated `_merge_params` return type from `Tuple[str, List[Diagnostic]]` to `Tuple[Dict[str, str], str, List[Diagnostic]]` to return both the merged dictionary and the formatted string.

2. Updated `_emit_instance` to capture the merged params dict and add it to `template_values` before props:
   ```python
   merged_params, params_str, param_diags = _merge_params(...)
   template_values.update(merged_params)  # Add individual params
   template_values.update(props)          # Add props (can override)
   ```

This allows templates to reference:
- `{name}`: instance name (implicit)
- `{ports}`: port connections (implicit)
- `{L}`, `{W}`, `{NF}`, `{m}`, etc.: individual merged params (new)
- `{model}`, etc.: backend props (existing)
- `{params}`: formatted param string (backward compat)

## Verification
- Tested with user's `examples/scratch/test.asdl` - successfully generated correct netlist with individual param substitution
- All existing unit tests pass: `pytest tests/unit_tests/netlist tests/unit_tests/ir tests/unit_tests/cli tests/unit_tests/e2e`

## Status
- Completed: 2026-01-03
- All tests passing
- Contract updated with decision log entry
