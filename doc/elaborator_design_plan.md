# ASDL Elaborator: Design and Refactoring Plan

This document outlines the design for the `Elaborator`, a new core component in the ASDL compilation pipeline, which replaces the former `PatternExpander`.

## 1. Rationale and Naming

- **From Expander to Elaborator**: The component's responsibility goes beyond simple pattern expansion. It will handle the entire "elaboration" phase, which involves transforming the abstract, parsed ASDL structure into a concrete, fully specified design.
- **Industry Alignment**: The term "elaboration" aligns with standard terminology used in Hardware Description Languages (like Verilog and VHDL), where this phase includes pattern expansion, parameter substitution, and generating a specific circuit instance from a generic template.

## 2. Core Responsibilities

The `Elaborator` will have two primary responsibilities:

1.  **Pattern Expansion**: Migrate and improve the logic from the old `PatternExpander`. This includes expanding differential pair (`<p,n>`) and bus (`[3:0]`) notations in ports, instance names, and mappings.
2.  **Parameter Resolution**: Resolve and substitute all parameter references (e.g., `{M_stage1}`). It will traverse the design hierarchy to determine the final, literal value for every parameter used in an instance. This logic will be moved out of the `SPICEGenerator`.

## 3. Architectural Approach

### Diagnostic-Based Error Handling

- **No Exceptions for Validation**: The `Elaborator` will **not** raise exceptions (`ValueError`) for validation errors (e.g., mismatched pattern counts, unresolved parameters).
- **Comprehensive Error Collection**: Instead, it will collect all errors and warnings into a list of `Diagnostic` objects. This allows the compiler/linter to report all issues in a file at once.
- **Robustness**: The elaboration process will attempt to continue even after finding errors, allowing for more complete analysis of a file.

### Public API

- The primary entry point will be the `elaborate` method.
- **Signature**: `def elaborate(self, asdl_file: ASDLFile) -> Tuple[ASDLFile, List[Diagnostic]]:`
- **Return Value**: It will always return a tuple containing the elaborated `ASDLFile` and the list of `Diagnostic` objects.

## 4. Implementation Plan

The `Elaborator` will be developed from scratch using a Test-Driven Development (TDD) approach.

1.  **Create New Files**:
    -   `src/asdl/elaborator.py`: The new implementation file.
    -   `tests/unit_tests/elaborator/`: A new test suite.
2.  **Incremental Migration**:
    -   Functionality from `PatternExpander` will be migrated piece by piece.
    -   For each feature, tests will be written first in the new suite, including tests for correct diagnostic reporting.
    -   The implementation will then be written in `elaborator.py` to make the tests pass.
3.  **Parameter Resolution Implementation**:
    -   New logic will be built within the `Elaborator` to handle parameter resolution.
    -   Tests will be created to cover various scenarios, including nested scopes and unresolved parameter errors.
4.  **Cleanup**:
    -   Once the new `Elaborator` is fully functional and tested, the old `src/asdl/expander.py` file and its tests will be deleted.
    -   Parameter substitution logic will be removed from `SPICEGenerator`.

This approach ensures a clean, robust, and well-tested implementation of a critical compiler component.
