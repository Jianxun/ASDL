# Generator TODOs

- Revisit PDK include path assumptions used during generation and tests.
  - Current test `tests/unit_tests/generator/test_generation_methods.py::test_pdk_include_generation_deduplicates` assumes includes like "{pdk}_fd_pr/models/ngspice/design.ngspice".
  - Evaluate per-PDK configurability, environment overrides, and technology libraries layout.
  - Consider moving path composition to a resolver utility with tests.


## Planned Diagnostics and Unit Tests

The generator should use diagnostics (XCCSS) rather than raising raw exceptions. The following diagnostics will be added with focused unit tests under `tests/unit_tests/generator/` (one file per error code):

- G0102: Top module not found
  - Severity: ERROR
  - Trigger: `file_info.top_module` is set, but that module key is absent from `asdl_file.modules`.
  - Behavior: Do not emit `XMAIN`; emit diagnostic G0102 with details: missing top name, available module names; add a helpful comment in header.
  - Comment example: `* ERROR G0102: top module 'top_name' not found; available: [a, b, c]`
  - Unit test: `tests/unit_tests/generator/test_g0102_top_module_not_found.py`
    - Create `ASDLFile(file_info.top_module="top")` with modules missing `top`.
    - Assert: diagnostic list contains code=="G0102"; no `XMAIN` present.

- G0301: Invalid module definition
  - Severity: ERROR
  - Trigger: A module has neither `spice_template` nor `instances` (invalid for generation).
  - Behavior: Emit diagnostic G0301 with module name; add a comment in the module subckt area; skip generation for that module.
  - Comment example: `* ERROR G0301: module 'foo' has neither spice_template nor instances`
  - Unit test: `tests/unit_tests/generator/test_g0301_invalid_module.py`
    - Create module with both fields `None`.
    - Assert: diagnostic code=="G0301"; no device/subckt lines emitted for that module.

- G0201: Unconnected port in subcircuit call (fatal)
  - Severity: ERROR
  - Trigger: An instance omits a declared port mapping; generator would otherwise emit `UNCONNECTED` placeholder.
  - Behavior: Treat as fatal; emit diagnostic G0201 identifying instance id, model, and missing port names; include a comment line at the offending call site and skip emitting that instance line.
  - Comment example: `* ERROR G0201: instance 'U1' of 'child' missing mappings for: ['b','c']`
  - Unit test: `tests/unit_tests/generator/test_g0201_unconnected_port.py`
    - Child module with ports [a,b,c]; parent instance maps only `a`.
    - Assert: diagnostic code=="G0201"; subckt contains an error comment and no `X_` call for that instance.

- I0701: Missing top module (informational)
  - Severity: INFO
  - Trigger: `file_info.top_module` is None/empty.
  - Behavior: Emit informational diagnostic indicating no `XMAIN` will be generated.
  - Comment example: `* INFO I0701: no top module specified; skipping main instantiation`
  - Unit test: `tests/unit_tests/generator/test_i0701_missing_top.py`
    - Create `ASDLFile` with `top_module=None`.
    - Assert: diagnostic code=="I0701"; no `XMAIN` present; otherwise valid `.end`.


### Notes on existing tests and overlap cleanup
- Unknown model reference is covered in `tests/unit_tests/generator/test_g0401_unknown_model.py` (canonical).
- PDK include presence stays covered in unified generation basics; deduplication is tested in `test_generation_methods`.
- Mixed primitive/hierarchical scenario moved to integration under `tests/integration/generator/test_mixed_design.py`.
