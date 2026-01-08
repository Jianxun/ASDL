# T-035 - IFIR conversion diagnostics spans

## Task summary
DoD:
- Decide how to map NFIR `src`/AST locations into IFIR conversion diagnostics.
- Add span-aware diagnostics (or document why spans are unavailable) for NFIR->IFIR conversion errors.
- Extend unit tests to cover diagnostics location behavior as needed.

Verify:
- `pytest tests/unit_tests/ir`

## Findings
- `src/asdl/ir/converters/nfir_to_ifir.py` always emits diagnostics with `primary_span=None` + `NO_SPAN_NOTE`, even though NFIR ops carry `src`.
- `src/asdl/emit/ngspice.py` does the same for emission errors; `InstanceOp`/`BackendOp`/`DeviceOp`/`ModuleOp` already have `src`.
- `src/asdl/ir/converters/ast_to_nfir.py` only sets `src` for module/device/backend; net/instance locations are not captured, so many spans are genuinely unavailable in the current AST model.
- Diagnostics are defined in terms of `SourceSpan`; using `LocationAttr` directly would require cross-cutting changes to renderers/sorting/JSON.

## Recommended fix
- Keep `LocationAttr` on IR ops and translate it to `SourceSpan` at diagnostic emission time.
- Add a small helper to convert `LocationAttr` to `SourceSpan` (support `FileLineColLoc`; return `None` for unknown locs).
- Update NFIR->IFIR converter and ngspice emitter to attach spans using `op.src` (or reasonable fallbacks).
- Document the limitation: without per-net/instance locations in AST/NFIR, some diagnostics will still be span-less.

## Proposed mapping details
Location translation:
- `location_attr_to_span(loc: LocationAttr | None) -> Optional[SourceSpan]`.
- If `loc` is `FileLineColLoc`, build `SourceSpan(file, line, col)` with end = start.
- For other `LocationAttr` variants, return `None`.

NFIR->IFIR converter (`src/asdl/ir/converters/nfir_to_ifir.py`):
- `INVALID_NFIR_DESIGN` (design has non module/device op): use offending op `src` if present.
- `INVALID_NFIR_DESIGN` (module has non net/instance op): use offending op `src` else module `src`.
- `UNKNOWN_ENDPOINT_INSTANCE`: use `net.src` (endpoint list location) else module `src`.
- `INVALID_NFIR_DEVICE` (device has non backend op): use offending op `src` else device `src`.
- Keep `NO_SPAN_NOTE` only when span is `None`.

ngspice emitter (`src/asdl/emit/ngspice.py`):
- Missing/unknown top: span `None` (no single source location).
- Unknown reference: use `instance.src`.
- Missing backend: use `device.src`.
- Missing/mismatched conns: use `instance.src`.
- Template errors and reserved placeholder warnings: use `backend.src`.
- Unknown instance param warning: use `instance.src`.

## Tests to add/update
- `tests/unit_tests/ir/test_ifir_converter.py`: construct NFIR ops with `FileLineColLoc` and assert `diagnostics[0].primary_span` is set for `UNKNOWN_ENDPOINT_INSTANCE` and invalid op cases.
- `tests/unit_tests/netlist/test_ngspice_emitter.py`: construct IFIR ops with `FileLineColLoc` and assert spans for missing conns/unknown ref/unknown param/template errors.
- Continue to accept `NO_SPAN_NOTE` when no `src` is set.

## Files likely touched
- `src/asdl/ir/converters/nfir_to_ifir.py`
- `src/asdl/emit/ngspice.py`
- `src/asdl/diagnostics/` (new helper module or utility)
- `tests/unit_tests/ir/test_ifir_converter.py`
- `tests/unit_tests/netlist/test_ngspice_emitter.py`

## Verify
- `pytest tests/unit_tests/ir`
- `pytest tests/unit_tests/netlist`

## Read
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.md`
- `agents/context/handoff.md`
- `src/asdl/ir/converters/ast_to_nfir.py`
- `src/asdl/ir/converters/nfir_to_ifir.py`
- `src/asdl/emit/ngspice.py`
- `src/asdl/ir/nfir/dialect.py`
- `src/asdl/ir/ifir/dialect.py`
- `venv/lib/python3.12/site-packages/xdsl/dialects/builtin.py`
- `tests/unit_tests/ir/test_ifir_converter.py`
- `tests/unit_tests/netlist/test_ngspice_emitter.py`

## Plan
1. Add a shared helper to translate `LocationAttr` into `SourceSpan`.
2. Wire span-aware diagnostics into NFIR->IFIR conversion and ngspice emission.
3. Extend unit tests to assert diagnostic spans for representative errors/warnings.
4. Run targeted tests for IR + netlist diagnostics.

## Progress log
- Added `location_attr_to_span` helper for `FileLineColLoc`.
- Updated NFIR->IFIR conversion diagnostics to attach spans from `src` when present.
- Updated ngspice diagnostics to attach spans for instance/device/backend issues.
- Extended IFIR converter and ngspice emitter unit tests to assert spans.

## Patch summary
- `src/asdl/ir/location.py`: new helper for `LocationAttr` -> `SourceSpan`.
- `src/asdl/ir/converters/nfir_to_ifir.py`: attach spans to diagnostics with fallbacks.
- `src/asdl/emit/ngspice.py`: attach spans in emission diagnostics.
- `tests/unit_tests/ir/test_ifir_converter.py`: add span assertions for converter errors.
- `tests/unit_tests/netlist/test_ngspice_emitter.py`: add span assertions for emitter diagnostics.

## PR URL
- https://github.com/Jianxun/ASDL/pull/35

## Verification
- `venv/bin/pytest tests/unit_tests/ir tests/unit_tests/netlist`
  - Result: 28 passed.

## Blockers / Questions
- None.

## Next steps
1. Run `pytest tests/unit_tests/ir`.
2. Run `pytest tests/unit_tests/netlist`.
3. Update `agents/context/handoff.md` with progress + verify results.
