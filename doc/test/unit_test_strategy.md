## Unit Test Strategy for ASDL (Lessons from Generator Refactor)

### Why this strategy
The generator suite was refactored from one verbose file into focused, fast, and intention‑revealing tests. This document captures the patterns that made the suite simpler, more maintainable, and more robust.

### Core principles
- **Diagnostics-first testing**: Prefer asserting XCCSS diagnostics over exceptions.
  - Error codes get their own files (e.g., `test_g0102_top_module_not_found.py`).
  - Assert both: diagnostic presence and helpful comment lines in generated output where applicable.
- **Public behavior over internals**: Test `SPICEGenerator.generate()` and `generate_subckt()` outputs, not private helpers.
- **Small, focused tests**: Keep each test focused on one behavior; avoid end‑to‑end bundling in unit tests.
- **MVP-friendly**: No back‑compat constraints; allow clean breaking changes that simplify the system.

### Directory and file organization
- **Unit tests**: `tests/unit_tests/<component>/`
  - **Diagnostics**: one file per code, e.g., `test_g0201_unconnected_port.py`, `test_g0301_invalid_module.py`.
  - **Feature slices**: concise files for primitives, hierarchical subckts, variables/templates, empty designs:
    - `test_primitives.py`
    - `test_hierarchical_subckt.py`
    - `test_variables_template.py`
    - `test_empty_design.py`
- **Integration tests**: `tests/integration/<component>/` for mixed scenarios and pipeline coverage (e.g., `test_mixed_design.py`).

### Diagnostic policy (Generator examples)
- **Codes covered**:
  - Errors: `G0102` (top not found), `G0201` (unconnected port), `G0301` (invalid module), `G0305` (unresolved placeholders), `G0401` (unknown model)
  - Warning: `G0601` (variable shadows parameter)
  - Info: `G0701` (no top specified)
- **Severity expectations**:
  - 01–05 → ERROR, 06 → WARNING, 07 → INFO
- **Assertions**:
  - Prefer `any(d.code == "Gxxxx" for d in diagnostics)` over full list equality
  - Also assert netlist contains `* ERROR/INFO/WARNING Gxxxx: ...` comment lines where relevant

### Assertion patterns that scale
- **Stable content checks only**:
  - Port order in `.subckt` headers is stable; assert exact header line
  - Parameter list ordering is defined (sorted by name); assert sorted order in strings
  - PDK includes deduplicate; assert count == 1 per PDK
- **Be tolerant of additive info**:
  - Allow informational diagnostics to appear (e.g., `G0701`) when no top is specified
  - Avoid asserting zero diagnostics unless that is the contract under test

### Test data construction
- **Inline, minimal fixtures**: Build `Module`/`Instance` objects inline for readability
- **Intentional invalids**: When bypassing dataclass guards (for negative tests), construct valid then mutate to invalid
- **No sys.path hacks**: Use `pyproject.toml` `pythonpath = ["."]` for import resolution under pytest

### When to choose integration tests
- Use unit tests for single behavior, single component
- Use integration tests for cross‑component flows (e.g., mixed primitive/hierarchical end‑to‑end netlisting)

### Template for adding a new diagnostic test
```python
from src.asdl.generator import SPICEGenerator
from src.asdl.data_structures import ASDLFile, FileInfo, Module, Instance

def test_gXXXX_meaningful_name():
    gen = SPICEGenerator()
    # Arrange: construct minimal ASDLFile to trigger the diagnostic
    asdl_file = ASDLFile(file_info=FileInfo(doc="Test"), modules={...})

    # Act
    output, diags = gen.generate(asdl_file)

    # Assert diagnostic and helpful comment
    assert any(d.code == "GXXXX" for d in diags)
    assert "GXXXX" in output
```

### Commit and workflow guidance
- **TDD loop**: write failing test → implement minimal change → make it pass → commit
- **Atomic commits**: keep tests and implementation together; use conventional commit messages
- **Speed**: keep unit tests fast; push heavier scenarios to integration tests

### Outcomes from the generator refactor
- Reduced a single, verbose suite into multiple focused files with clearer intent
- Eliminated back‑compat baggage and redundant assertions
- Strengthened diagnostics coverage with explicit tests per error code
- Preserved public behavior guarantees while enabling rapid iteration

