# ASDL Implementation Plan

## Overview
This document outlines the detailed implementation plan for the ASDL (Analog Structured Description Language) project. The goal is to build a complete pipeline: YAML → Parser → Expander → Resolver → Generator → SPICE.

## Phase 1: Data Structure Enhancements

### 1.1 ASDLFile Round-trip & Debug Methods
**Priority: High**

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

### 1.2 Data Structure Corrections
**Priority: High**

**Issue Found:** The example YAML uses `design_info` but the code expects `file_info`. Need to handle both for backwards compatibility during parsing.

## Phase 2: Parser Implementation

### 2.1 Complete YAML Parser
**Priority: High**

Replace all placeholder `# TODO` implementations in `parser.py`:

#### 2.1.1 FileInfo Parsing
- Handle both `design_info` (legacy) and `file_info` (v0.4)
- Validate required fields
- Provide meaningful defaults

#### 2.1.2 Models Parsing  
- Parse device model definitions
- Validate `DeviceType` enum values
- Handle optional description field
- Convert port lists properly

#### 2.1.3 Modules Parsing
- Parse module definitions with all components
- Handle optional fields (doc, nets, parameters)
- Recursive parsing of ports, instances, etc.

#### 2.1.4 Ports Parsing
- Parse port definitions with direction and type
- Handle constraints (placeholder implementation)
- Validate enum values for `PortDirection` and `SignalType`

#### 2.1.5 Instance Parsing
- Parse instance definitions
- Preserve mappings and parameters as-is (no expansion yet)
- Handle optional intent metadata

### 2.2 Error Handling
**Priority: Medium**

Comprehensive error handling for:
- File not found
- YAML syntax errors  
- Invalid ASDL structure
- Missing required fields
- Invalid enum values
- Type mismatches

## Phase 3: Pattern Expander Implementation

### 3.1 Differential Pattern Expansion
**Priority: High**

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
**Priority: High**

Implement expansion of `[high:low]` patterns:

```python  
# Input:  "data[3:0]"
# Output: ["data[3]", "data[2]", "data[1]", "data[0]"]
```

### 3.3 Net Pattern Expansion
**Priority: Medium**

Extend pattern expansion to `nets.internal` declarations.

## Phase 4: Parameter Resolver Implementation

### 4.1 Expression Evaluation
**Priority: High**

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
**Priority: High**

- Module parameters provide context for instance parameters
- Parameter inheritance and override semantics
- Error handling for undefined parameters

### 4.3 Context Management
**Priority: Medium**

- Track parameter scopes
- Handle parameter shadowing
- Provide clear error messages for resolution failures

## Phase 5: SPICE Generator Implementation

### 5.1 Subcircuit Generation
**Priority: High**

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
**Priority: High**

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
**Priority: High**

- Header comments with file metadata
- Proper subcircuit ordering (dependencies first)
- Top-level instantiation handling
- `.end` statement

### 5.4 Error Handling
**Priority: Medium**

- Unconnected ports → "UNCONNECTED" nets
- Missing model references
- Invalid parameter values

## Phase 6: Integration & Testing

### 6.1 Pipeline Integration
**Priority: High**

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
**Priority: High**

#### 6.2.1 Unit Tests
- Each component tested independently
- Mock data for isolated testing
- Edge cases and error conditions

#### 6.2.2 Integration Tests  
- End-to-end pipeline testing
- Real ASDL examples (inverter, OTA)
- Round-trip testing (YAML → ASDLFile → YAML)

#### 6.2.3 JSON Debug Testing
- Verify JSON serialization works
- Test with complex nested structures
- Ensure human-readable output

### 6.3 Example Validation
**Priority: Medium**

- Verify existing examples parse correctly
- Generate SPICE for all examples
- Validate SPICE syntax

## Phase 7: Code Quality & Documentation

### 7.1 Code Cleanup
**Priority: Medium**

- Remove all `# TODO` placeholders
- Add comprehensive docstrings
- Type hints validation
- Error message improvements

### 7.2 API Documentation
**Priority: Low**

- Generate API docs from docstrings
- Usage examples
- Error handling guide

## Implementation Order

1. **Data Structure Enhancements** (ASDLFile methods)
2. **Parser Implementation** (handle existing examples)  
3. **Pattern Expander** (differential first, then bus)
4. **Parameter Resolver** (simple first, then arithmetic)
5. **SPICE Generator** (basic structure, then refinements)
6. **Integration & Testing** (continuous throughout)
7. **Code Quality** (final cleanup)

## Success Criteria

- [ ] Parse `examples/inverter.yml` successfully
- [ ] Parse `examples/two_stage_ota.yml` successfully  
- [ ] Generate valid SPICE netlist for both examples
- [ ] Round-trip: YAML → ASDLFile → YAML (original files)
- [ ] JSON debug output for all data structures
- [ ] All tests pass
- [ ] No `# TODO` comments remain in core functionality

## Risk Mitigation

1. **Complex Pattern Expansion**: Start with simple differential patterns
2. **Unsafe Expression Evaluation**: Implement safe evaluator early
3. **YAML Compatibility**: Handle both legacy and v0.4 formats
4. **SPICE Syntax**: Validate against ngspice documentation

## Dependencies

- PyYAML: YAML parsing and generation
- JSON: Built-in Python module for debug output
- Dataclasses: For clean data structure definitions
- Enum: Type-safe enumeration values
- Typing: Type hints for better code quality 