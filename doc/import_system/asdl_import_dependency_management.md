# ASDL Import Abstraction Strategy Summary

## Core Philosophy
**Complete separation of design logic from physical implementation through explicit import mapping**

## Unified Import Mechanism

### **Single Import Syntax for All Dependencies**
```yaml
imports:
  local_alias: qualified.source.name
```

### **Three Dependency Types, One Syntax**
```yaml
imports:
  # PDK primitive files
  pdk_primitives: gf180mcu_pdk.primitives
  
  # Design IP files  
  amplifiers: analog_ip.amplifiers
  
  # SPICE primitive libraries (always implicit)
  # analoglib: analoglib  # Implicit - always available
```

### **Module References with Qualified Names**
```yaml
instances:
  M1: {model: pdk_primitives.nfet_03v3}        # PDK primitive module
  AMP: {model: amplifiers.two_stage_miller}    # Design IP module
  VDC: {model: analoglib.vdc}                  # SPICE primitive
```

## Unit Device Abstraction

### **Three-Layer Architecture**

**Layer 1: PDK Primitives** (Raw SPICE device models)
```yaml
# gf180mcu_pdk/primitives.asdl - Direct PDK primitive access
modules:
  nfet_03v3:
    ports: [D, G, S, B]
    parameters: {L: 0.28u, W: 3u, NF: 2, M: 1}
    spice_template: MN {D} {G} {S} {B} nfet_03v3 L={L} W={W} nf={NF} m={M}
    pdk: gf180mcu
```

**Layer 2: Unit Devices** (Standardized device tiles with fixed geometry)
```yaml
# gf180mcu_std_tiles/devices.asdl - Unit devices wrapping PDK primitives
imports:
  pdk_primitives: gf180mcu_pdk.primitives

modules:
  # Unit devices with fixed geometry, multiplier-only interface
  nmos_unit_short:
    ports: [D, G, S, B]
    parameters: {M: 1}
    instances:
      M1:
        model: pdk_primitives.nfet_03v3
        mappings: {D: D, G: G, S: S, B: B}
        parameters: {L: 0.28u, W: 3u, NF: 2, M: "{M}"}
        
  nmos_unit_long:
    ports: [D, G, S, B] 
    parameters: {M: 1}
    instances:
      M1:
        model: pdk_primitives.nfet_03v3
        mappings: {D: D, G: G, S: S, B: B}
        parameters: {L: 0.5u, W: 3u, NF: 2, M: "{M}"}
```

**Layer 3: Design Logic** (Technology-independent, multiplier-only)
```yaml
# Design files import unit devices, focus on topology
imports:
  std_devices: gf180mcu_std_tiles.devices

modules:
  current_mirror:
    instances:
      M_REF:  {model: std_devices.nmos_unit_short, parameters: {M: 1}}    # Reference
      M_OUT1: {model: std_devices.nmos_unit_short, parameters: {M: 2}}    # 2x current  
      M_OUT2: {model: std_devices.nmos_unit_short, parameters: {M: 4}}    # 4x current
```

## Key Benefits

### **1. Technology Independence**
- Same design works across PDKs - only imports change
- Circuit topology remains unchanged
- True IP portability across technology nodes

### **2. Design Exploration Flexibility**
```yaml
# Easy technology swapping - same design logic
imports:
  std_devices: gf180mcu_std_tiles.devices     # GF180MCU technology
  # std_devices: sky130_std_tiles.devices     # Sky130 technology  
  # std_devices: tsmc28_std_tiles.devices     # TSMC28 technology

# Design logic remains unchanged
instances:
  M1: {model: std_devices.nmos_unit_short, parameters: {M: 2}}
```

### **3. Clear Design Intent**
- Multiplier ratios show designer intent directly
- Matching requirements obvious from identical multipliers
- Current/size relationships explicit

### **4. Clean Dependency Management**
- All dependencies declared explicitly in imports section
- Design body remains unchanged when dependencies change
- Easy A/B testing of different implementations

## Library Discovery and File Organization

### **Centralized Library Registry**
```yaml
# asdl.lib.yaml (project or system level)
libraries:
  gf180mcu_pdk: /shared/pdks/gf180mcu_pdk
  gf180mcu_std_tiles: /shared/pdks/gf180mcu_std_tiles
  sky130_pdk: /shared/pdks/sky130_pdk  
  sky130_std_tiles: /shared/pdks/sky130_std_tiles
  analog_ip: ./libs/analog_ip
  my_project_ip: ./design/ip_blocks
```

### **File Organization Structure**
```
gf180mcu_pdk/
  primitives.asdl         # Contains: nfet_03v3, pfet_03v3, bjt_npn, etc.
  
gf180mcu_std_tiles/
  devices.asdl            # Contains: nmos_unit_short, nmos_unit_long, etc.
  
analog_ip/
  amplifiers.asdl         # Contains: two_stage_miller, folded_cascode, etc.
  filters.asdl            # Contains: butterworth_lpf, chebyshev_hpf, etc.
```

### **Import Resolution Rules**
**RULE: Imports always point to specific .asdl files**

```yaml
imports:
  # Format: alias: library.filename
  pdk_primitives: gf180mcu_pdk.primitives        # → gf180mcu_pdk/primitives.asdl
  std_devices: gf180mcu_std_tiles.devices        # → gf180mcu_std_tiles/devices.asdl
  amplifiers: analog_ip.amplifiers               # → analog_ip/amplifiers.asdl
  
# Module references: alias.module_name
instances:
  M1: {model: pdk_primitives.nfet_03v3}          # Module in primitives.asdl
  M2: {model: std_devices.nmos_unit_short}       # Module in devices.asdl
  A1: {model: amplifiers.two_stage_miller}       # Module in amplifiers.asdl
```

**Resolution Rule**: `alias: library.filename` → `library/filename.asdl`

### **Multi-Module File Support**
ASDL supports multiple modules per file through existing data structures:
- ✅ **No parser changes needed** - `modules:` section already exists
- ✅ **Simple import resolution** - import file, then reference modules
- ✅ **Library organization** - group related devices/circuits in single file
- ✅ **Backward compatibility** - existing single-module files work unchanged

```yaml
# Example: analog_ip/amplifiers.asdl
file_info:
  doc: "Operational amplifier IP library"
  version: "1.2.0"
  date: "2024-03-15"

modules:
  two_stage_miller: {...}
  folded_cascode: {...}
  telescopic: {...}
  
# Usage: Import file, then reference modules
imports:
  amplifiers: analog_ip.amplifiers@1.2.0    # Optional version tag

instances:
  OTA: {model: amplifiers.two_stage_miller}  # Module in amplifiers.asdl
```

## Implementation Strategy

### **Phase 1 (MVP)**
- Implement explicit import mapping syntax
- Support unit device abstraction with multipliers
- Basic PDK primitive and design cell imports

### **Phase 2**
- Add unit device libraries for common PDKs
- Tooling for automatic unit device characterization
- Enhanced versioning and dependency management
- Corner binding precedence rules (requires discussion)
- Behavioral fallback mechanisms (requires discussion)

### **Deferred Complexity**
- Workspace-level library management
- Complex resolution order rules
- Multi-PDK support

## Advanced Usage: Parameterized Imports

### **Simulation Sweeps and Design Exploration**

**Parameterized Import Syntax:**
```yaml
parameters:
  device_variant: nmos_unit_short  # Default
  ota_impl: two_stage_miller      # Default

imports:
  std_devices: gf180mcu_std_tiles.devices
  amplifiers: analog_ip.amplifiers

instances:
  M1: {model: std_devices.${device_variant}, parameters: {M: 2}}
  AMP: {model: amplifiers.${ota_impl}, ...}
```

### **Device Variant Sweeps**
```yaml
# Testbench can sweep device types
testbench_parameters:
  device_variants:
    - nmos_unit_short    # Short channel, fast
    - nmos_unit_long     # Long channel, matched

# Each simulation run uses different device variant
sweep:
  parameter: device_variant
  values: ${device_variants}  # Expands to std_devices.{variant}
```

### **Implementation Comparison**
```yaml
# Compare different OTA implementations in same LDO
imports:
  amplifiers: analog_ip.amplifiers
  extracted: analog_ip.extracted
  behavioral: analog_ip.behavioral

testbench_parameters:
  ota_implementations:
    - amplifiers.two_stage_miller      # Standard design
    - amplifiers.folded_cascode        # High gain option  
    - extracted.two_stage_extracted    # Post-layout netlist
    - behavioral.ota_model             # Fast simulation

# Sweep PSRR performance across implementations
sweep:
  parameter: ota_impl
  values: ${ota_implementations}
  metrics: [psrr_60hz, psrr_1khz, settling_time]
```

### **Model Fidelity Progression**
```yaml
# Development workflow: behavioral → schematic → extracted
imports:
  # Phase 1: Fast behavioral models
  behavioral: analog_ip.behavioral
  
  # Phase 2: Detailed schematic simulation  
  # amplifiers: analog_ip.amplifiers
  
  # Phase 3: Post-layout verification
  # extracted: analog_ip.extracted

instances:
  # Reference modules within imported files
  OTA: {model: behavioral.${ota_impl}, ...}     # Phase 1
  # OTA: {model: amplifiers.${ota_impl}, ...}  # Phase 2  
  # OTA: {model: extracted.${ota_impl}, ...}   # Phase 3
```

### **Cross-PDK Comparison**
```yaml
parameters:
  pdk_variant: gf180mcu  # Default

imports:
  std_devices: ${pdk_variant}_std_tiles.devices

# Compare same design across PDKs
instances:
  M1: {model: std_devices.nmos_unit_short, parameters: {M: 2}}
  M2: {model: std_devices.pmos_unit_short, parameters: {M: 1}}

testbench_sweep:
  pdk_variants: [gf180mcu, sky130, tsmc28]
  metrics: [gain, bandwidth, power]
```

## Benefits of Parameterized Imports

### **1. Automated Design Space Exploration**
- Sweep device variants to optimize performance
- Compare multiple IP implementations automatically
- Statistical analysis across parameter spaces

### **2. Progressive Model Fidelity**
- Start with behavioral models for fast iteration
- Move to schematic models for accuracy
- Verify with extracted netlists
- Single design file works at all fidelity levels

### **3. Cross-Technology Validation**
- Same design verified across multiple PDKs
- Technology migration risk assessment
- Process sensitivity analysis

### **4. Regression Testing**
- Automated testing of IP library updates
- Performance tracking across design revisions
- Continuous integration for analog designs

## Result
**Analog designs become topology-focused like digital designs**, with physical implementation details abstracted into reusable unit device libraries. Designers work with logical relationships and ratios rather than transistor geometry.

**Advanced parameterization enables systematic design exploration** comparable to digital design flows, with automated sweeps across device variants, implementations, and technology nodes.

## Design Decisions and Implementation Rules

### **1. Namespace Resolution Policy** 
**RULE: Always qualified names for cross-library references**

```yaml
# ✅ CORRECT: Always use qualified names pointing to files
imports:
  pdk_primitives: gf180mcu_pdk.primitives        # File import
  std_devices: gf180mcu_std_tiles.devices        # File import
  
instances:
  M1: {model: pdk_primitives.nfet_03v3}          # Module reference
  M2: {model: std_devices.nmos_unit_short}       # Module reference

# ❌ FORBIDDEN: Ambiguous imports
# imports:
#   pdk: gf180mcu_pdk                             # Ambiguous - directory or file?
#   nfet_03v3: gf180mcu_pdk.primitives.nfet_03v3 # Too specific - imports point to files
```

**Local References Within Same File:**
```yaml
# ✅ ALLOWED: Unqualified references within same file
modules:
  nfet_03v3: {...}           # Defined locally
  nmos_wrapper:
    instances:
      M1: {model: nfet_03v3} # Local reference - no qualification needed
```

### **2. Corner Management Strategy**
**RULE: Corners are runtime bindings, orthogonal to imports**

```yaml
# ✅ CORRECT: Corners specified at testbench level
type: testbench
corners:
  gf180mcu: {mos: ff, bjt: typical}  # Runtime corner binding
  
imports:
  design: my_project.ldo_design      # Corner-agnostic import

# Corners applied during SPICE generation:
# .lib "gf180mcu_fd_pr/models/ngspice/design.ngspice" ff
```

**Corner Binding Precedence:**
- **RULE**: Corner binding always applies last, after all parameterization
- Import elaboration resolves dependencies without corner information
- Parameter substitution happens during elaboration
- Corner binding happens during SPICE generation phase
- Same elaborated design can be simulated at different corners

```yaml
# Example: Parameterized import with corner binding
imports:
  models: analog_ip.${fidelity}     # Parameterized import

instances:
  OTA: {model: models.${ota_impl}}  # Parameter substitution first

# Corner binding applied last during SPICE generation
corners:
  gf180mcu: {mos: ff}               # Applied to final resolved model
```

### **3. File-Based Import Conventions**
**RULE: Imports always point to specific .asdl files**

```yaml
# Import syntax: alias: library.filename
imports:
  amplifiers: analog_ip.amplifiers        # Points to amplifiers.asdl file
  filters: analog_ip.filters              # Points to filters.asdl file
  
# Module references: alias.module_name
instances:
  OTA: {model: amplifiers.two_stage_miller}
  LPF: {model: filters.butterworth_lpf}
```

**Clear Resolution Rule:**
- `library.filename` → `library/filename.asdl`
- No ambiguity about directories vs files vs modules
- Every import explicitly identifies one .asdl file

### **4. Version and Metadata Requirements**
**RULE: All .asdl files must include version and date metadata**

```yaml
# ✅ REQUIRED: Version metadata in all files
file_info:
  doc: "Description of the library/module"
  version: "1.2.0"        # REQUIRED - semantic version
  date: "2024-03-15"      # REQUIRED - last modified date
  author: "Team/Contact"  # Optional but recommended

# Optional version tags in imports (recommended for reproducibility)
imports:
  amplifiers: analog_ip.amplifiers@1.2.0    # Version-specific import
  primitives: gf180mcu_pdk.primitives       # Latest version (not recommended)
```

**Version Enforcement Policy:**
- **ERROR**: Missing `version` or `date` in `file_info`
- **WARNING**: Import without version tag (reproducibility risk)
- **INFO**: Version mismatch between expected and actual

### **5. Unit Device Philosophy**
**RULE: Start with multiplier-only, evolve to meta-parameters**

**Phase 1 (MVP): Multiplier-only interface**
```yaml
nmos_unit_short:
  parameters: {M: 1}  # Only multiplier exposed
```

**Phase 2: Meta-parameter expansion to avoid variant explosion**
```yaml
nmos_unit:
  parameters: 
    M: 1
    vt_type: regular      # enum: [regular, low_vt, high_vt]
    channel_length: short # enum: [short, standard, long]
  # Avoids creating nmos_unit_short_low_vt, nmos_unit_long_high_vt, etc.
```

### **6. Primitive vs Hierarchical Enforcement**
**RULE: `spice_template` and `instances` are mutually exclusive**

```yaml
# ✅ PRIMITIVE: Has spice_template, renders inline
vdc:
  spice_template: V{name} {plus} {minus} DC={DC}
  # No instances field allowed

# ✅ HIERARCHICAL: Has instances, becomes subcircuit  
amplifier:
  instances: {...}
  # No spice_template field allowed
  
# ❌ FORBIDDEN: Cannot have both
# hybrid_device:
#   spice_template: "..."  # Error: mutually exclusive
#   instances: {...}       # Error: mutually exclusive
```

**Multi-Line Template Validation Rules:**
```yaml
# ✅ ALLOWED in spice_template:
# - SPICE device statements (R, C, L, M, Q, D, X, etc.)
# - Parameter substitution {param}
# - Comments (lines starting with *)
# - Node names and instance names

# ❌ FORBIDDEN in spice_template:  
# - .subckt definitions (use instances instead)
# - Control statements (.if, .param, .func, etc.)
# - Simulator directives (.include, .lib, .options)
# - Analysis statements (.ac, .dc, .tran, etc.)
```

**Complex Device Strategy:**
```yaml
# For complex primitives, use multi-line SPICE templates
bjt_with_parasitics:
  spice_template: |
    QN {C} {B} {E} npn_10x10 area={area} dtemp={mismatch}
    R_CB {C} {B} R={parasitic_r}
    C_CB {C} {B} C={parasitic_c}
  parameters: {area: 1, mismatch: 0, parasitic_r: 100, parasitic_c: 10f}
  # Still primitive - no instances field

# Multi-line templates allow complex device modeling
# without breaking primitive vs hierarchical separation
esd_protection:
  spice_template: |
    D1 {A} {gnd} diode_esd area={area}
    R1 {A} {A_int} R=50
    C1 {A_int} {gnd} C=100f
  parameters: {area: 10}
```

### **7. SPICE Generation Strategy**

**Two-Stage Compilation**: 
1. **Import Elaboration** → Resolve all imports into single self-contained ASDL file
2. **SPICE Generation** → Emit netlist from fully elaborated design (no import handling needed)

**PDK Include Generation**: `pdk` field drives `.include` statements
```yaml
nfet_03v3:
  spice_template: MN {D} {G} {S} {B} nfet_03v3 L={L} W={W}
  pdk: gf180mcu  # → .include "gf180mcu_fd_pr/models/ngspice/design.ngspice"
```

## Future Enhancements

### **Phase 2 Features**
- **Enhanced Versioning**: Version enforcement with warnings for missing tags
- **Meta-Parameter Unit Devices**: Enum-based parameters to reduce variant explosion
- **Enhanced Diagnostics**: Clear error messages with import resolution suggestions

### **Phase 3 Features**  
- **Auto-Generation Tooling**: PDK → unit device library automation
- **Elaboration Caching**: Performance optimization for large designs
- **Behavioral Model Fallback**: Search order and graceful degradation (deferred - requires discussion)
- **Advanced Template Features**: Complex validation and optimization