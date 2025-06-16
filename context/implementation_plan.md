# ASDL Implementation Plan

## Overview
This document outlines the detailed implementation plan for the ASDL (Analog Structured Description Language) project. The goal is to build a complete pipeline: YAML → Parser → Expander → Resolver → Generator → SPICE.

## Current Sprint: SPICE Generator Implementation (Phase 5)

**Status:** Parser implementation complete (44 passing tests). Now implementing SPICE netlist generator using TDD approach.

**Current Priority:** Implement SPICE generator with comprehensive test coverage following the test structure:
1. Device Generation Tests (`test_device_generation.py`)
2. Net and Port Tests (`test_nets_and_ports.py`) 
3. Module/Subcircuit Tests (`test_module_generation.py`)
4. Complete SPICE Output Tests (`test_spice_output.py`)
5. Parameter Handling Tests (`test_parameters.py`)
6. Error Handling Tests (`test_error_handling.py`)
7. Metadata and Comments Tests (`test_metadata.py`)
8. Integration Tests (`test_integration.py`)

## Phase 1: Data Structure Enhancements ✅ COMPLETED

### 1.1 ASDLFile Round-trip & Debug Methods
**Status: PENDING - Next Sprint**

Add the following methods to `ASDLFile` class:

```python
def to_yaml(self) -> str:
    """Convert ASDLFile back to YAML string (round-trip)."""

def save_to_file(self, filepath: str) -> None:
    """Save ASDLFile to YAML file (round-trip)."""

def to_json(self) -> str:
    """Convert ASDLFile to JSON string for debugging."""

def dump_json(self, filepath: str) -> None:
    """Save ASDLFile as JSON file for debugging."""
```

**Requirements:**
- Round-trip only guaranteed for **original** ASDLFile (before expansion/resolution)
- JSON output must be human-readable for debugging
- Handle all dataclass types and nested structures
- Preserve YAML schema structure

### 1.2 Data Structure Corrections ✅ COMPLETED
**Issue Resolved:** Updated schema from `design_info` to `file_info` with backward compatibility.

## Phase 2: Parser Implementation ✅ COMPLETED

**Status:** Complete with 44 passing tests using systematic TDD approach.

✅ **Achievements:**
- Complete YAML parser with future-proofing capabilities
- FileInfo parsing with backward compatibility (`design_info` → `file_info`)
- Models parsing with device model definitions and validation
- Modules parsing with all components and recursive structures
- Ports parsing with direction, type, and constraint handling
- Instance parsing with mapping and parameter preservation
- Comprehensive error handling for all error cases
- Configurable strict/lenient validation modes
- Unknown field detection and handling
- Intent metadata preservation for extensibility

## Phase 3: Pattern Expander Implementation

### 3.1 Differential Pattern Expansion
**Priority: High - Future Sprint**

Implement expansion of `<p,n>` patterns:

```python
# Input:  "in_<p,n>"
# Output: ["in_p", "in_n"]
```

#### 3.1.1 Port Pattern Expansion
- Handle patterns in port names
- Create separate Port objects for each expanded name
- Preserve all port attributes

#### 3.1.2 Instance Pattern Expansion  
- Handle patterns in instance names
- Create separate Instance objects
- Coordinate mapping expansion with instance expansion

#### 3.1.3 Mapping Pattern Expansion
- Order-matched expansion: i-th expanded port → i-th expanded net
- Handle complex patterns in both port and net names

### 3.2 Bus Pattern Expansion  
**Priority: High - Future Sprint**

Implement expansion of `[high:low]` patterns:

```python  
# Input:  "data[3:0]"
# Output: ["data[3]", "data[2]", "data[1]", "data[0]"]
```

### 3.3 Net Pattern Expansion
**Priority: Medium - Future Sprint**

Extend pattern expansion to `nets.internal` declarations.

## Phase 4: Parameter Resolver Implementation

### 4.1 Expression Evaluation
**Priority: High - Future Sprint**

#### 4.1.1 Simple Parameter References
```python
# Input:  "$M" with context {"M": 4}
# Output: 4
```

#### 4.1.2 Arithmetic Expressions
```python
# Input:  "$M*4" with context {"M": 2} 
# Output: 8
```

#### 4.1.3 Safe Expression Evaluator
**Critical:** Replace unsafe `eval()` with restricted arithmetic evaluator:
- Allow: `+, -, *, /, (, )`
- Allow: Numbers and parameter references
- Forbid: Function calls, imports, dangerous operations

### 4.2 Hierarchical Parameter Resolution
**Priority: High - Future Sprint**

- Module parameters provide context for instance parameters
- Parameter inheritance and override semantics
- Error handling for undefined parameters

### 4.3 Context Management
**Priority: Medium - Future Sprint**

- Track parameter scopes
- Handle parameter shadowing
- Provide clear error messages for resolution failures

## Phase 5: SPICE Generator Implementation 🚧 CURRENT SPRINT

### 5.1 Subcircuit Generation
**Priority: High - IN PROGRESS**

#### 5.1.1 Module → .subckt
- Generate `.subckt` headers with proper port ordering
- Handle module documentation as comments
- Generate `.ends` properly

#### 5.1.2 Port Ordering Convention
**Decision Required:** Define consistent port ordering:
- Option A: Alphabetical order
- Option B: Declaration order (preserve YAML order)
- Option C: Explicit ordering field

### 5.2 Instance Generation
**Priority: High - IN PROGRESS**

#### 5.2.1 Device Instance → Device Line
```spice
# Format: <name> <nodes> <model> <parameters>
MN1 drain gate source bulk nch_lvt W=1u L=0.1u M=1
```

#### 5.2.2 Module Instance → Subcircuit Call
```spice  
# Format: X<name> <nodes> <subckt_name>
XINV1 in out vdd vss inverter
```

### 5.3 Netlist Structure
**Priority: High - IN PROGRESS**

- Header comments with file metadata
- Proper subcircuit ordering (dependencies first)
- Top-level instantiation handling
- `.end` statement

### 5.4 Error Handling
**Priority: Medium - IN PROGRESS**

- Unconnected ports → "UNCONNECTED" nets
- Missing model references
- Invalid parameter values

## Phase 6: Integration & Testing

### 6.1 Pipeline Integration
**Priority: High - Future Sprint**

Create end-to-end pipeline:
```python
def asdl_to_spice(yaml_file: str) -> str:
    parser = ASDLParser()
    expander = PatternExpander()  
    resolver = ParameterResolver()
    generator = SPICEGenerator()
    
    asdl = parser.parse_file(yaml_file)
    expanded = expander.expand_patterns(asdl)
    resolved = resolver.resolve_parameters(expanded)
    spice = generator.generate(resolved)
    return spice
```

### 6.2 Test Suite Development
**Priority: High - ONGOING**

#### 6.2.1 Unit Tests ✅ PARSER COMPLETE
- Parser: 44 passing tests with comprehensive coverage
- Generator: TDD in progress with 8 test modules planned

#### 6.2.2 Integration Tests  
**Priority: Medium - Future Sprint**
- End-to-end pipeline testing
- Real ASDL examples (inverter, OTA)
- Round-trip testing (YAML → ASDLFile → YAML)

#### 6.2.3 JSON Debug Testing
**Priority: Medium - Future Sprint**
- Verify JSON serialization works
- Test with complex nested structures
- Ensure human-readable output

### 6.3 Example Validation
**Priority: Medium - Future Sprint**

- Verify existing examples parse correctly ✅ DONE
- Generate SPICE for all examples
- Validate SPICE syntax

## Phase 7: Code Quality & Documentation

### 7.1 Code Cleanup
**Priority: Medium - Future Sprint**

- Remove all `# TODO` placeholders
- Add comprehensive docstrings
- Type hints validation
- Error message improvements

### 7.2 API Documentation
**Priority: Low - Future Sprint**

- Generate API docs from docstrings
- Usage examples
- Error handling guide

## Implementation Order - UPDATED

1. ✅ **Data Structure Enhancements** (Basic classes complete, round-trip methods pending)
2. ✅ **Parser Implementation** (Complete with 44 passing tests)  
3. 🚧 **SPICE Generator** (Current sprint - TDD in progress)
4. **Pattern Expander** (differential first, then bus)
5. **Parameter Resolver** (simple first, then arithmetic)
6. **Integration & Testing** (continuous throughout)
7. **Code Quality** (final cleanup)

## Success Criteria - UPDATED

- ✅ Parse `examples/inverter.yml` successfully
- ✅ Parse `examples/two_stage_ota.yml` successfully  
- [ ] **Generate valid SPICE netlist for both examples** (CURRENT GOAL)
- [ ] Round-trip: YAML → ASDLFile → YAML (original files)
- [ ] JSON debug output for all data structures
- ✅ Parser tests pass (44/44)
- [ ] **SPICE generator tests pass** (IN PROGRESS)
- [ ] No `# TODO` comments remain in core functionality

## Risk Mitigation

1. **Complex Pattern Expansion**: Start with simple differential patterns (DEFERRED)
2. **Unsafe Expression Evaluation**: Implement safe evaluator early (FUTURE)
3. ✅ **YAML Compatibility**: Handle both legacy and v0.4 formats (COMPLETED)
4. **SPICE Syntax**: Validate against ngspice documentation (CURRENT FOCUS)

## Dependencies

- PyYAML: YAML parsing and generation ✅
- JSON: Built-in Python module for debug output
- Dataclasses: For clean data structure definitions ✅
- Enum: Type-safe enumeration values ✅
- Typing: Type hints for better code quality ✅ 