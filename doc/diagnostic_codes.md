# ASDL Diagnostic Codes

This document serves as the single source of truth for all diagnostic codes used in the ASDL toolchain. It provides a centralized reference for understanding error and warning messages, their meanings, and how to resolve them.

## Code Structure

Diagnostic codes are structured to be easily identifiable and searchable.

- **Prefix**: A letter indicating the component where the diagnostic originates.
  - `P`: Parser
  - `E`: Elaborator
  - `V`: Validator
  - `G`: Generator
  - `S`: Serialization
- **Number**: A three-digit number identifying the specific diagnostic.
  - **100-199**: Errors (prevent successful compilation)
  - **200-299**: Warnings (indicate potential issues but do not stop compilation)

---

## **P: Parser**
*Diagnostics related to syntax and basic document structure.*

| Code   | Title                     | Implementation Status | Test Coverage |
| :----- | :------------------------ | :-------------------- | :------------ |
| **P100**   | Invalid YAML Syntax       | ✅ Implemented       | ✅ Covered    |
| **P101**   | Invalid Root Type         | ✅ Implemented       | ✅ Covered    |
| **P102**   | Missing Required Section  | ❌ Not Implemented   | ❌ Not Covered|
| **P103**   | Invalid Section Type      | ❌ Not Implemented   | ❌ Not Covered|
| **P200**   | Unknown Top-Level Section | ❌ Not Implemented   | ❌ Not Covered|
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

---

## **E: Elaborator**
*Diagnostics related to pattern expansion and parameter resolution.*

| Code   | Title                          | Implementation Status | Test Coverage |
| :----- | :----------------------------- | :-------------------- | :------------ |
| **E100**   | Empty Pattern                  | ✅ Implemented       | ✅ Covered    |
| **E101**   | Single-Item Pattern            | ✅ Implemented       | ✅ Covered    |
| **E102**   | Pattern Count Mismatch         | ✅ Implemented       | ✅ Covered    |
| **E103**   | Mixed Pattern Types            | ✅ Implemented       | ❌ Not Covered|
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