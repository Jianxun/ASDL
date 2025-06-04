# ASDL to SPICE Implementation Plan

## Overview
Convert ASDL YAML to hierarchical SPICE netlists while preserving module structure as `.subckt` blocks. Focus on simple, agile prototype development.

## Core Design Principles
- **Preserve Hierarchy**: Each ASDL `module` → SPICE `.subckt`
- **Pattern Expansion**: Handle `{p,n}` style symmetric device generation
- **Parameter Resolution**: Resolve `${param}` expressions in context
- **Simple Architecture**: Minimal classes, straightforward data flow
- **Prototype First**: Get basic functionality working, then iterate

## Architecture Overview

```
ASDL YAML → Parser → Pattern Expander → Parameter Resolver → SPICE Generator
     ↓            ↓              ↓                ↓              ↓
  Raw Dict → Module Objects → Expanded Devices → Resolved Params → .subckt blocks
```

## Core Components

### 1. Data Model (`src/asdl/models.py`)
Simple dataclasses to represent the parsed structure:

```python
@dataclass
class ASDLModule:
    name: str
    nets: Dict[str, str]           # net_name -> role
    parameters: Dict[str, Any]     # param hierarchies
    circuits: List[Circuit]        # devices + submodule instances
    notes: Dict[str, Any]          # design intent

@dataclass  
class Circuit:
    name: str
    model: str                     # device type or module name
    nets: Dict[str, str]           # pin -> net mappings
    parameters: Dict[str, Any]     # device parameters (M, L, W, etc.)
    
@dataclass
class ASDLFile:
    version: str
    top_module: str
    defaults: Dict[str, Any]       # YAML anchors
    modules: Dict[str, ASDLModule]
```

### 2. YAML Parser (`src/asdl/parser.py`)
```python
class ASDLParser:
    def parse_file(self, filepath: str) -> ASDLFile:
        # Load YAML with anchor resolution (PyYAML handles this)
        # Convert to ASDLFile object
        # Basic validation
        
    def _parse_module(self, name: str, data: dict) -> ASDLModule:
        # Handle nets with pattern expansion: {in_{p,n}: in}
        # Parse parameters (scalars or nested dicts)
        # Parse circuits list
```

### 3. Pattern Expander (`src/asdl/expander.py`)
```python
class PatternExpander:
    def expand_patterns(self, module: ASDLModule) -> ASDLModule:
        # Expand {p,n} patterns in device names and nets
        # Example: MN_{P,N} → [MN_P, MN_N]
        # Handle parallel expansion: name/nets must align
        
    def _expand_braces(self, pattern: str) -> List[str]:
        # "{p,n}" → ["p", "n"]
        # "{1,2,3}" → ["1", "2", "3"]  
        # "MN_{P,N}" → ["MN_P", "MN_N"]
```

### 4. Parameter Resolver (`src/asdl/resolver.py`)
```python
class ParameterResolver:
    def resolve_parameters(self, module: ASDLModule, 
                          context: Dict[str, Any]) -> ASDLModule:
        # Resolve ${param} and ${param.sub} expressions
        # Handle hierarchical parameter passing
        # Support simple math: ${M.diff * 2}
        
    def _substitute_expression(self, expr: str, context: dict) -> Any:
        # "${M.diff}" → context["M"]["diff"]
        # "${Cc}" → context["Cc"]
```

### 5. SPICE Generator (`src/asdl/spice_generator.py`)
```python
class SPICEGenerator:
    def generate(self, asdl_file: ASDLFile) -> str:
        # Generate hierarchical SPICE with .subckt blocks
        # Process modules in dependency order
        # Emit primitives as device instances
        
    def _generate_subckt(self, module: ASDLModule) -> str:
        # .subckt module_name pin1 pin2 ...
        # ... device instances ...
        # .ends module_name
        
    def _generate_device(self, circuit: Circuit) -> str:
        # MN1 d g s b nmos_unit M=4 L=180n W=2u
```

## Implementation Phases

### Phase 1: Basic Parser (Week 1)
- [x] Project setup complete
- [ ] Implement basic YAML loading with anchor resolution
- [ ] Create simple data model classes
- [ ] Parse one example file (ota_two_stg.yaml)
- [ ] Write basic tests for parser

### Phase 2: Pattern Expansion (Week 1)
- [ ] Implement brace pattern expansion `{p,n}`
- [ ] Handle device name expansion: `MN_{P,N}`
- [ ] Handle net name expansion: `out_{p,n}`
- [ ] Test with symmetric differential pairs

### Phase 3: Parameter Resolution (Week 2)
- [ ] Implement `${param}` substitution
- [ ] Handle nested parameters: `${M.diff}`
- [ ] Support hierarchical parameter passing
- [ ] Test parameter inheritance through module hierarchy

### Phase 4: SPICE Generation (Week 2)
- [ ] Generate `.subckt` blocks for each module
- [ ] Handle primitive device instances
- [ ] Manage hierarchical module instantiation
- [ ] Produce clean, readable SPICE output

### Phase 5: Integration & Testing (Week 3)
- [ ] End-to-end conversion pipeline
- [ ] Test with multiple example circuits
- [ ] SPICE syntax validation
- [ ] Error handling and diagnostics

## Key Implementation Details

### Pattern Expansion Strategy
```python
# Input: name: "MN_{P,N}", nets: {D: "out_{p,n}"}
# Output: [
#   Circuit(name="MN_P", nets={D: "out_p"}),
#   Circuit(name="MN_N", nets={D: "out_n"})
# ]
```

### Parameter Context Management
```python
# Hierarchical parameter resolution:
# Top level: M: {diff: 4, tail: 8}
# Module instantiation: M: ${M.diff}
# Context chain: global_params → module_params → instance_params
```

### SPICE Output Structure
```spice
* Generated from ota_two_stg.yaml
* ASDL v1.0

.subckt diff_pair_nmos in_p in_n out_p out_n tail
MN_P tail out_p in_p VSS nmos_unit M=2
MN_N tail out_n in_n VSS nmos_unit M=2
.ends diff_pair_nmos

.subckt ota_one_stage in_p in_n vbn out vdd vss
X_diff in_p in_n n_d out n_tail diff_pair_nmos
MN_TAIL n_tail vss vbn VSS nmos_unit M=4
X_load n_d out vdd current_mirror_pmos_1_1
.ends ota_one_stage

.subckt ota in_p in_n out iref vdd vss
X_vbn_gen iref vbn vss bias_vbn_diode
X_stage1 in_p in_n vbn stg1_out vdd vss ota_one_stage  
X_stage2 stg1_out out vbn vdd vss common_source_amp
Cc stg1_out out capacitor_unit M=1pF
.ends ota
```

## Error Handling Strategy
- **Validation**: Check required fields, detect circular dependencies
- **Debugging**: Preserve source location info for error messages  
- **Graceful degradation**: Continue processing when possible
- **Clear diagnostics**: Point to exact YAML line for errors

## Testing Strategy
- **Unit tests**: Each component independently
- **Integration tests**: Full ASDL → SPICE pipeline
- **Golden reference**: Compare outputs with known-good netlists
- **SPICE validation**: Check generated netlists parse correctly

## Tools & Dependencies
- **PyYAML**: YAML parsing with anchor support
- **pytest**: Testing framework
- **click**: CLI interface (future)
- **dataclasses**: Simple data model classes

## Success Metrics
1. Successfully convert `ota_two_stg.yaml` → working SPICE
2. Generated SPICE loads without errors in simulator
3. Hierarchical structure preserved (readable subcircuits)
4. Pattern expansion works for differential pairs
5. Parameter substitution resolves correctly
6. Clean, maintainable code for continued iteration

---

*This plan prioritizes getting a working prototype quickly while maintaining clean architecture for future extension.* 