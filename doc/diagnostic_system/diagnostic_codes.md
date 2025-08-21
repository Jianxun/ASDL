# ASDL Diagnostic Codes

This document serves as the single source of truth for all diagnostic codes used in the ASDL toolchain. It provides a centralized reference for understanding error and warning messages, their meanings, and how to resolve them.

## Code Structure

> ⚠️ **Migration Notice**: This document describes the current (legacy) diagnostic system. A new XCCSS format is planned for implementation. See [XCCSS Design Documentation](xccss_design_decisions.md) for details about the future system.

Diagnostic codes are structured to be easily identifiable and searchable.

### Current System (Legacy)

- **Prefix**: A letter indicating the component where the diagnostic originates.
  - `P`: Parser
  - `E`: Elaborator
  - `V`: Validator
  - `G`: Generator
  - `S`: Serialization
- **Number**: A three-digit number identifying the specific diagnostic.
  - **100-199**: Errors (prevent successful compilation)
  - **200-299**: Warnings (indicate potential issues but do not stop compilation)

### Planned XCCSS System

The future diagnostic system will use a structured `XCCSS` format:
- **X**: Component prefix (P, E, V, G, I, S)
- **CC**: Category code (01-08: Syntax, Schema, Semantic, Reference, Type, Style, Extension, Performance)
- **SS**: Specific error code within category (01-99)

**Migration Timeline**: See [XCCSS Migration Plan](xccss_migration_plan.md) for implementation schedule.

---

## **P: Parser**
*Diagnostics related to syntax and basic document structure.*

| Code   | Title                     | Implementation Status | Test Coverage |
| :----- | :------------------------ | :-------------------- | :------------ |
| **P100**   | Invalid YAML Syntax       | ✅ Implemented       | ✅ Covered    |
| **P101**   | Invalid Root Type         | ✅ Implemented       | ✅ Covered    |
| **P102**   | Missing Required Section  | ✅ Implemented       | ✅ Covered    |
| **P103**   | Invalid Section Type      | ❌ Not Implemented   | ❌ Not Covered|
| **P104**   | Missing Required Field    | ❌ Not Implemented   | ❌ Not Covered|
| **P106**   | Invalid Import Format     | ✅ Implemented       | ✅ Covered    |
| **P107**   | Module Type Conflict      | ✅ Implemented       | ✅ Covered    |
| **P108**   | Incomplete Module Definition | ✅ Implemented    | ✅ Covered    |
| **P200**   | Unknown Top-Level Section | ✅ Implemented       | ✅ Covered    |
| **P201**   | Unknown Field             | ❌ Not Implemented   | ❌ Not Covered|

### P100: Invalid YAML Syntax
- **Type**: `Error`
- **Component**: `Parser`
- **Title**: `Invalid YAML Syntax`
- **Details**: The file could not be parsed because it does not conform to YAML syntax rules. This is often caused by incorrect indentation, missing colons, or invalid characters.
- **Example (Incorrect)**:
  ```yaml
  file_info
    top_module: "test" # Missing colon
  ```
- **Suggestion**: Review the file for syntax errors, paying close attention to indentation and the use of special characters.

### P101: Invalid Root Type
- **Type**: `Error`
- **Component**: `Parser`
- **Title**: `Invalid Root Type`
- **Details**: The root of an ASDL file must be a dictionary (a set of key-value pairs). The parser found a list or a single value instead.
- **Example (Incorrect)**:
  ```yaml
  - file_info:
      top_module: "test"
  ```
- **Suggestion**: Ensure the ASDL file starts with a key-value structure, not a list (indicated by a leading `-`).

### P102: Missing Required Section
- **Type**: `Error`
- **Component**: `Parser`
- **Title**: `Missing Required Section`
- **Details**: A mandatory top-level section (like `file_info`) is missing from the ASDL file.
- **Example (Incorrect)**:
  ```yaml
  # 'file_info' section is missing
  modules:
    ...
  ```
- **Suggestion**: Add the missing mandatory section to the file.

### P103: Invalid Section Type
- **Type**: `Error`
- **Component**: `Parser`
- **Title**: `Invalid Section Type`
- **Details**: The section type is not recognized or supported by the parser.
- **Example (Incorrect)**:
  ```yaml
  # 'file_info' section is missing
  modules:
    ...
  ```
- **Suggestion**: Ensure the section type is valid and supported by the parser.

### P104: Missing Required Field
- **Type**: `Error`
- **Component**: `Parser`
- **Title**: `Missing Required Field`
- **Details**: A mandatory field is missing from the ASDL file.
- **Example (Incorrect)**:
  ```yaml
  # 'file_info' section is missing
  modules:
    ...
  ```
- **Suggestion**: Add the missing mandatory field to the file.

### P106: Invalid Import Format
- **Type**: `Error`
- **Component**: `Parser`
- **Title**: `Invalid Import Format`
- **Details**: Import declarations must follow the format `alias: library.filename` or `alias: library.filename@version`. The import source must contain at least one dot to separate library and filename.
- **Example (Incorrect)**:
  ```yaml
  imports:
    bad_import: "justfilename"  # Missing library.filename format
  ```
- **Suggestion**: Use format 'alias: library.filename' or 'alias: library.filename@version'.

### P107: Module Type Conflict
- **Type**: `Error`
- **Component**: `Parser`
- **Title**: `Module Type Conflict`
- **Details**: A module cannot have both 'spice_template' and 'instances' fields. These fields define mutually exclusive module types: primitive (spice_template) or hierarchical (instances).
- **Example (Incorrect)**:
  ```yaml
  modules:
    conflicted_module:
      spice_template: "M {D} {G} {S} {B} nch"
      instances:  # This conflicts with spice_template
        M1: ...
  ```
- **Suggestion**: Remove either 'spice_template' (to make hierarchical) or 'instances' (to make primitive).

### P108: Incomplete Module Definition
- **Type**: `Error`
- **Component**: `Parser`
- **Title**: `Incomplete Module Definition`
- **Details**: Every module must be either a primitive module (with 'spice_template') or a hierarchical module (with 'instances'). A module without either field is incomplete.
- **Example (Incorrect)**:
  ```yaml
  modules:
    incomplete_module:
      ports:
        in: { direction: input }
      # Missing either spice_template or instances
  ```
- **Suggestion**: Add either 'spice_template' for primitive modules or 'instances' for hierarchical modules.

---

## **E: Elaborator**
*Diagnostics related to pattern expansion and parameter resolution.*

| Code   | Title                          | Implementation Status | Test Coverage |
| :----- | :----------------------------- | :-------------------- | :------------ |
| **E100**   | Empty Pattern                  | ✅ Implemented       | ✅ Covered    |
| **E101**   | Single-Item Pattern            | ✅ Implemented       | ✅ Covered    |
| **E102**   | Pattern Count Mismatch         | ✅ Implemented       | ✅ Covered    |
| **E103**   | Mixed Pattern Types            | ✅ Implemented       | ✅ Covered    |
| **E104**   | Invalid Bus Range              | ❌ Not Implemented   | ❌ Not Covered|
| **E105**   | Undefined Parameter            | ❌ Not Implemented   | ❌ Not Covered|
| **E106**   | Malformed Parameter Expression | ❌ Not Implemented   | ❌ Not Covered|
| **E107**   | Empty Pattern Item             | ✅ Implemented       | ✅ Covered    |


### E100: Empty Pattern
- **Type**: `Error`
- **Component**: `Elaborator`
- **Title**: `Empty Pattern`
- **Details**: A literal pattern `<>` cannot be empty. It must contain items to expand.
- **Example (Incorrect)**:
  ```yaml
  ports:
    in<>:
      direction: input
  ```
- **Suggestion**: Provide at least two comma-separated items inside the pattern brackets, like `in<p,n>`.

### E101: Single-Item Pattern
- **Type**: `Error`
- **Component**: `Elaborator`
- **Title**: `Single-Item Pattern`
- **Details**: A literal pattern must contain at least two items to be meaningful. A pattern with one item provides no expansion benefit.
- **Example (Incorrect)**:
  ```yaml
  ports:
    in<p>:
      direction: input
  ```
- **Suggestion**: Ensure the pattern contains at least two items, like `in<p,n>`, or remove the pattern syntax if only a single port is needed (`in_p`).

### E102: Pattern Count Mismatch
- **Type**: `Error`
- **Component**: `Elaborator`
- **Title**: `Pattern Count Mismatch`
- **Details**: When mapping patterns, the number of items in the instance pattern must exactly match the number of items in the net pattern.
- **Example (Incorrect)**:
  ```yaml
  instances:
    M<1,2>:
      model: my_model
      mappings:
        D: out<1,2,3> # Mismatch: instance has 2 items, net has 3
  ```
- **Suggestion**: Ensure that patterns being mapped to each other have the same number of comma-separated items.

### E103: Mixed Pattern Types
- **Type**: `Error`
- **Component**: `Elaborator`
- **Title**: `Mixed Pattern Types`
- **Details**: A name cannot contain both a literal pattern (`<>`) and a bus pattern (`[]`). This creates ambiguity.
- **Example (Incorrect)**:
  ```yaml
  ports:
    data<[0],[1]>:
      direction: input
  ```
- **Suggestion**: Choose one pattern type for a given name. Use multiple declarations if necessary.

### E107: Empty Pattern Item
- **Type**: `Error`
- **Component**: `Elaborator`
- **Title**: `Empty Pattern Item`
- **Details**: All items provided in a literal pattern were empty strings (e.g., `sig<,>`). While empty strings can be part of a pattern (e.g., `sig<p,,n>`), at least one item must be non-empty.
- **Example (Incorrect)**:
  ```yaml
  ports:
    "sig<,>":
      direction: input
  ```
- **Suggestion**: Ensure that at least one item inside the pattern is a non-empty string.

---

## **V: Validator**
*Diagnostics related to semantic and logical failures in the fully elaborated design.*

| Code   | Title                      | Implementation Status | Test Coverage |
| :----- | :------------------------- | :-------------------- | :------------ |
| **V100**   | Undefined Module           | ❌ Not Implemented   | ❌ Not Covered|
| **V101**   | Undefined Model            | ❌ Not Implemented   | ❌ Not Covered|
| **V102**   | Circular Module Dependency | ❌ Not Implemented   | ❌ Not Covered|
| **V103**   | Duplicate Definition       | ❌ Not Implemented   | ❌ Not Covered|
| **V104**   | Name Collision             | ❌ Not Implemented   | ❌ Not Covered|
| **V105**   | Invalid Port Connection    | ❌ Not Implemented   | ❌ Not Covered|
| **V200**   | Unused Module/Model        | ✅ Implemented       | ✅ Covered    |
| **V201**   | Unused Port/Net            | ❌ Not Implemented   | ❌ Not Covered|
| **V202**   | Undeclared Net Usage       | ✅ Implemented       | ✅ Covered    |
| **V203**   | Floating Input Port        | ❌ Not Implemented   | ❌ Not Covered|

### V200: Unused Module/Model
- **Type**: `Warning`
- **Component**: `Validator` (Currently in Generator)
- **Title**: `Unused Module/Model`
- **Details**: A module or device model was defined in the ASDL file but was not instantiated anywhere in the design hierarchy starting from the top module.
- **Example (Incorrect)**:
  ```yaml
  modules:
    unused_module: # This module is never used
      ...
    top:
      instances:
        ...
  ```
- **Suggestion**: Remove the unused module or model definition to keep the design files clean.

### V202: Undeclared Net Usage
- **Type**: `Warning`
- **Component**: `Validator` (Currently in Generator)
- **Title**: `Undeclared Net Usage`
- **Details**: A net name was used in an instance mapping but was not declared as a port or an internal net within the module's scope.
- **Example (Incorrect)**:
  ```yaml
  modules:
    my_module:
      ports:
        in: { direction: input }
      instances:
        M1:
          model: my_model
          mappings:
            D: out # 'out' is not declared as a port or internal_net
  ```
- **Suggestion**: Declare the net in the module's `ports` or `internal_nets` section. 