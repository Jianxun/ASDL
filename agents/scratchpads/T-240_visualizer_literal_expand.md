# T-240: Expand literal patterns in visualizer dump + add numeric labels

## Scope
- Expand literal enum patterns in instance names and endpoint pin names for visualizer dump.
- Keep numeric ranges compact; attach per-endpoint numeric labels formatted `<3>` or `<3,1>`.
- Join multiple slices with `;` per `docs/specs/spec_asdl_pattern_expansion.md`.

## Files
- `src/asdl/core/dump.py`
- `src/asdl/core/registries.py`
- `src/asdl/patterns_refactor/`

## Notes
- Ensure `ota_nmos.asdl` dump includes endpoints for `mn_tail.<s|b>` and `mn_in_<n>.d`.
- Do not expand numeric ranges in visualizer view.

## Verify
- `./venv/bin/asdlc visualizer-dump examples/libs/mosbius_devices/ota_nmos/ota_nmos.asdl`
