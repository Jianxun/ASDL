# ASDL Data Structure Design

This document outlines the refined design for the core data structures in `src/asdl/data_structures.py`. The goal of this redesign is to improve clarity, enforce the single responsibility principle, and create a robust foundation for the ASDL linter and compiler.

## 1. Serialization and I/O

### Decision

All serialization and file I/O logic will be removed from the data classes and moved into a dedicated `src/asdl/serialization.py` module.

### Rationale

-   **Single Responsibility Principle:** The responsibility of a data class (like `ASDLFile`) is to represent data. The responsibility of converting that data to a specific format (JSON, YAML) belongs to a dedicated serializer.
-   **Decoupling:** The core data structures will have no dependency on `PyYAML` or other formatting libraries, making them more portable and easier to test.
-   **Clarity:** This separation makes the purpose of each module clearer to developers.

### Proposed Structure

**`src/asdl/data_structures.py`** will contain only pure data classes. For example, `ASDLFile` will be simplified to:

```python
@dataclass
class ASDLFile:
    """
    Represents a single ASDL file with its modules.
    (This class will contain no serialization methods).
    """
    file_info: 'FileInfo'
    modules: Dict[str, 'Module']
```

**`src/asdl/serialization.py`** will contain all conversion and file-writing logic:

```python
# src/asdl/serialization.py (Conceptual)

def asdl_to_dict(asdl_file: ASDLFile) -> dict:
    # ... logic using dataclasses.asdict ...

def asdl_to_json_string(asdl_file: ASDLFile) -> str:
    # ... logic using json.dumps and a custom encoder ...

def save_asdl_to_yaml_file(asdl_file: ASDLFile, filepath: str):
    # ... logic to serialize and write to a file ...
```

## 2. Unified Module Architecture

### Decision

The architecture has been unified to use only `Module` objects. Primitive devices are now represented as modules with a `primitive_type` field, eliminating the separate `DeviceModel` class.

### Rationale

-   **Simplification:** A single `Module` class can represent both hierarchical modules and primitive devices, reducing complexity.
-   **Consistency:** All components in the design hierarchy use the same data structure, making tools and algorithms more uniform.
-   **Clarity:** The distinction between primitives and hierarchical modules is made through the `primitive_type` field rather than separate classes.

### Current Structure

Primitive modules are distinguished by the presence of a `primitive_type` field:

```python
@dataclass
class Module:
    """
    Unified representation for both hierarchical modules and primitive devices.
    """
    ports: Optional[Dict[str, Port]] = None
    internal_nets: Optional[List[str]] = None
    parameters: Optional[Dict[str, Any]] = None
    variables: Optional[Dict[str, Any]] = None
    instances: Optional[Dict[str, Instance]] = None
    primitive_type: Optional[str] = None  # Present only for primitive modules
    device_line: Optional[str] = None     # SPICE template for primitives
    metadata: Optional[Dict[str, Any]] = None
```

## 3. Internal Net Declaration

### Decision

The `Nets` class will be eliminated. It will be replaced by a new field, `internal_nets: Optional[List[str]]`, directly on the `Module` class.

### Rationale

-   **Simplicity:** The original structure (`module.nets.internal`) was unnecessarily nested. Having a direct list of internal nets on the module is cleaner and more intuitive.
-   **Clarity:** Naming the field `internal_nets` is explicit and unambiguous, preventing confusion with nets that are implicitly declared by ports. This improves the self-documenting nature of the ASDL schema.

### Proposed Structure

The `Nets` class will be removed. The `Module` class will be updated:

```python
@dataclass
class Module:
    # ...
    ports: Optional[Dict[str, Port]] = None
    internal_nets: Optional[List[str]] = None # Replaces the Nets class
    parameters: Optional[Dict[str, Any]] = None
    instances: Optional[Dict[str, Instance]] = None
```

## 4. Universal Metadata Field

### Decision

A universal, free-form `metadata: Optional[Dict[str, Any]]` field will be added to all major ASDL data structures. This field will replace the specialized `intent` field on the `Instance` class.

### Rationale

-   **Extensibility:** Provides a consistent mechanism to add annotations, tool-specific data, or design intent without requiring future schema changes.
-   **Uniformity:** Creates a single, predictable place for metadata across all levels of the ASDL hierarchy (from the top-level file down to individual ports).
-   **Consolidation:** The `intent` field on `Instance` was a good first step, but generalizing it to a `metadata` field makes the system more robust and scalable.

### Proposed Implementation

A `Metadata` type alias will be defined for clarity:

```python
from typing import Dict, Any, Optional

Metadata = Dict[str, Any]
```

This `metadata: Optional[Metadata]` field will be added to the following data classes:
- `ASDLFile`
- `FileInfo`
- `Port`
- `Module`
- `Instance` (replacing `intent`) 