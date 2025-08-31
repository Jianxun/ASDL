## Parser Unit Test Suite Refactor Plan

### Goals
- **Explain each existing parser test case** and map to diagnostics
- **Identify redundancies** to consolidate
- **Map tests → error codes** and list codes without coverage
- **Flag tests needing new codes** or code/doc alignment
- **Propose a clean file structure** for the refactored suite

### Inventory: Current tests and diagnostics mapping

- `tests/unit_tests/parser/test_basic_parsing.py`
  - `test_parse_minimal_valid_yaml`: Happy path minimal parse; asserts `ASDLFile` fields and location metadata. No diagnostics expected.
  - `test_parse_file_success`: Happy path from file; ensures `file_path` captured. No diagnostics expected.
  - `test_parse_file_not_found`: IO behavior raising `FileNotFoundError` (exception).
  - `test_parse_invalid_yaml_syntax`: Malformed YAML → P100.
  - `test_parse_non_dictionary_root`: Non-dict root → P101.
  - `test_parse_empty_yaml`: Empty string returns `(None, [])` (no diagnostic).

- `tests/unit_tests/parser/test_error_handling.py` (overlaps with above)
  - `test_toplevel_is_not_a_dictionary`: Non-dict root → P101 scenario (asserts details/severity/location, not code explicitly).
  - `test_yaml_syntax_error`: Malformed YAML → P100 scenario (asserts details/severity/location, not code explicitly).

- `tests/unit_tests/parser/test_location_tracking.py`
  - `test_file_info_location`, `test_module_location`, `test_port_location`, `test_instance_location`: Verifies line/column metadata for `FileInfo`, `Module`, `Port`, `Instance`. No diagnostics expected.

- `tests/unit_tests/parser/test_model_alias_parser.py`
  - Valid `model_alias`: no diagnostics.
  - Missing dot / non-string values: P0503 (Invalid Model Alias Format). Asserts code/title/severity; preserves valid entries.
  - Empty/None section: no diagnostics.

- `tests/unit_tests/parser/test_structural_diagnostics.py`
  - `test_missing_file_info_section`: Missing `file_info` → P102.
  - `test_invalid_modules_section_type`: `modules` not a dict → P103.
  - `test_unknown_top_level_section`: Unknown top-level key → P200 (warning) with location.

- `tests/unit_tests/parser/test_unified_parsing.py`
  - `test_models_section_rejected`: Legacy `models` section → P200 (warning); ignored during parsing.
  - `test_unified_module_parsing`: Happy-path mixed primitive/hierarchical parsing; no diagnostics.
  - `test_parser_enforces_mutual_exclusion`: Both `spice_template` and `instances` → P107.
  - `test_parser_requires_implementation`: Neither `spice_template` nor `instances` → P0231.
  - `test_imports_section_parsing`: Expects rich import model (`ImportDeclaration`, alias/version), no diagnostics.
  - `test_invalid_import_format`: Expects two invalid import errors → P0501/P0502.
  - `test_empty_imports_section`: No imports → no diagnostics; `imports` is `None`.
  - `test_unified_parser_preserves_location_info`: Sanity check for location in imports/modules; redundant with dedicated location tests.

- `tests/unit_tests/parser/test_unknown_field_warnings.py`
  - Unknown field in module/port/instance → P0702 (warning). Multiple warnings supported. Known fields only → no diagnostics.

- `tests/unit_tests/parser/test_parameter_variable_dual_syntax.py`
  - Canonical/abbreviated `parameters` and `variables` at module/instance levels parse without diagnostics; stored canonically.
  - Both forms in same scope → warning expected; should map to P0601 (parameters) and P0602 (variables). Current tests do not assert codes explicitly.

### Redundancies to consolidate
- **P100/P101 YAML/root**: Duplicated across `test_basic_parsing.py` and `test_error_handling.py`. Keep a single focused file that asserts code, severity, details, and location.
- **P200 Unknown top-level**: Covered by generic unknown key and legacy `models`. Keep one canonical parameterized test (e.g., keys: `models`, `future_feature`); drop the duplicate.
- **Location assertions**: Keep comprehensive checks only in `test_location_tracking.py`. Remove redundant location checks from `test_unified_parsing.py`.

### Implementation vs test direction (Imports)
- Decision finalized: Parser uses simple file-path imports (`imports: { alias: "path/to/file.asdl" }`). Rich `library.filename[@version]` objects are obsolete.
- Consolidate import diagnostics into Parser P-codes per XCCSS:
  - P0501: Invalid Import Path Type (non-string)
  - P0502: Invalid Import File Extension (must end with `.asdl`)
- Tests must drop P106 and `ImportDeclaration` expectations and assert P0501/P0502 with simple string mapping.

### Coverage map: implemented codes hit by tests
- YAML/root: P100, P101 (covered). Empty file: returns no diag (covered behavior).
- Sections: P0201 (missing `file_info`) and P0202 (section not dict) covered.
- Modules semantic: P0230 (conflict) and P0231 (incomplete) covered.
- Unknown sections/fields: P0701 (unknown top-level) and P0702 (unknown field) covered.
- Model alias: P0503 covered.
- Dual syntax warnings: Behavior covered, but codes **P301/P302** not asserted explicitly.
- Imports: Tests currently expect P106 (outdated). Parser should emit P0501/P0502; add/adjust tests accordingly.

### Implemented behaviors lacking tests
- P104: Missing required field used in two contexts by current code:
  - Port missing `dir` (PortParser) → P104 (not tested).
  - Instance missing `model` (InstanceParser) → P104 (not tested).
- P105: Port parsing exception (e.g., bad enum conversion) → P105 (not tested).
- P0501/P0502: Import path type/extension diagnostics need tests (replace old P106 expectations).
- P301/P302: Dual syntax warnings emitted, tests don’t assert codes explicitly.

### Spec’d codes without coverage (and often not implemented)
- High priority (duplicates/imports):
  - P0232: Duplicate Module Name — no tests, not implemented.
  - P0242: Duplicate Port Name — no tests, not implemented.
  - P0251: Duplicate Instance Name — no tests, not implemented.
  - P0221: Duplicate Import Alias — no tests, not implemented.
  - P0501: Invalid Import Path Type — tests to add; implement in parser.
  - P0502: Invalid Import File Extension — tests to add; implement in parser.

### New/adjusted codes recommended
- Empty file diagnostic (optional): Introduce informational code (e.g., P0103 “Empty File”) so empty content returns an INFO diagnostic instead of silent `(None, [])`.
- Consider splitting generic **P104** into specific codes per spec alignment:
  - P0240 “Missing Port Direction” (ports);
  - P0250 “Missing Instance Model” (instances).
  If retaining P104, update the error-code doc to reflect current implementation.

### Proposed refactored file structure

```
tests/unit_tests/parser/
  test_yaml_and_root.py            # P100, P101, (P0103 if added)
  test_toplevel_sections.py        # P102, P103, P200 (parameterized)
  test_model_alias.py              # P0503
  test_modules_semantics.py        # P107, P108
  test_ports.py                    # P104 (missing dir), P105, P0501, P0502
  test_instances.py                # P104 (missing model); dual-syntax at instance level
  test_dual_syntax.py              # P301, P302 (assert codes)
  test_unknown_fields.py           # P201
  test_location_tracking.py        # location metadata checks
  test_imports_parser.py           # P0501 (type) and P0502 (extension)
```

### High-priority test additions (TDD)
- Ports: P0240 for missing `dir`; P0205 for generic conversion failure; P0511/P0512 for enum.
- Instances: P0250 for missing `model`.
- Dual syntax: Assert **P0601** and **P0602** codes in existing warning tests.
- Imports: Add tests for P0501 (non-string) and P0502 (non-.asdl).

### Medium-priority test additions (drive new implementation)
- Duplicate detection: P0232, P0242, P0251, P0221.
- Enum validation: P0501, P0502 with clear suggestion messages.

### Action items
- Introduce parser XCCSS diagnostics module mirroring generator approach; migrate legacy P-codes where appropriate.
- Consolidate duplicate YAML/root and P200 tests; remove redundant location assertions elsewhere.
- Add missing P104/P105 tests; start asserting P301/P302.
- Implement P0501/P0502 in ImportParser and align tests.
- Schedule TDD for duplicate detection to reach MVP coverage.

### Notes
- Remove ad-hoc `sys.path` manipulation in tests; rely on `pyproject.toml` `pythonpath = ["."]` for test imports.

