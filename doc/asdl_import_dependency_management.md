# ASDL Import Abstraction Strategy Summary

## Core Philosophy
**Complete separation of design logic from physical implementation through explicit import mapping**

## Unified Import Mechanism

### **Single Import Syntax for All Dependencies**
```yaml
imports:
  local_name: qualified.source.name
```

### **Three Dependency Types, One Syntax**
```yaml
imports:
  # Analog standard cells (unit devices from PDK wrapper library)
  nmos_unit: gf180mcu_analog_std_lib.devices.nmos_unit_L0p28
  pmos_unit: gf180mcu_analog_std_lib.devices.pmos_unit_L0p28
  
  # Design cells from libraries  
  bias_gen: analog_ip.bandgap_bias
  opamp: analog_ip.amplifiers.two_stage_miller
  
  # External SPICE cells
  esd_cell: padlib.esd_protection
```

## Unit Device Abstraction

### **Three-Layer Architecture**

**Layer 1: PDK Primitives** (Only in analog standard cell libraries)
```yaml
# gf180mcu_analog_std_lib/devices.asdl
file_info:
  doc: "GF180MCU analog standard cell library"

models:
  nfet_03v3: {...}  # PDK primitive reference
  pfet_03v3: {...}

modules:
  nmos_unit_L0p28:
    ports:
      D: {dir: in_out, type: voltage}
      G: {dir: in, type: voltage}
      S: {dir: in_out, type: voltage}
      B: {dir: in_out, type: voltage}
    instances:
      M1:
        model: nfet_03v3
        mappings: {D: D, G: G, S: S, B: B}
        parameters: {L: 0.28u, W: 3u, NF: 2, m: 1}
        
  nmos_unit_L0p5:
    ports: {D: {...}, G: {...}, S: {...}, B: {...}}
    instances:
      M1:
        model: nfet_03v3
        mappings: {D: D, G: G, S: S, B: B}
        parameters: {L: 0.5u, W: 3u, NF: 2, m: 1}
        
  pmos_unit_L0p28:
    ports: {D: {...}, G: {...}, S: {...}, B: {...}}
    instances:
      M1:
        model: pfet_03v3
        mappings: {D: D, G: G, S: S, B: B}
        parameters: {L: 0.28u, W: 6u, NF: 2, m: 1}
```

**Layer 2: Analog Standard Cells** (Unit devices with fixed geometry)
```yaml
# Design files import unit devices, never PDK primitives
imports:
  nmos_unit: gf180mcu_analog_std_lib.devices.nmos_unit_L0p28
  pmos_unit: gf180mcu_analog_std_lib.devices.pmos_unit_L0p28
```

**Layer 3: Design Logic** (Geometry-free, multiplier-only)
```yaml
# 1:2:4 current mirror - only topology and ratios
instances:
  M_REF:  {model: nmos_unit, params: {m: 1}}    # Reference
  M_OUT1: {model: nmos_unit, params: {m: 2}}    # 2x current
  M_OUT2: {model: nmos_unit, params: {m: 4}}    # 4x current
```

## Key Benefits

### **1. Technology Independence**
- Same design works across PDKs - only imports change
- Circuit topology remains unchanged
- True IP portability across technology nodes

### **2. Design Exploration Flexibility**
```yaml
# Easy device variant swapping
imports:
  nmos_unit: gf180mcu_analog_std_lib.devices.nmos_unit_L0p28     # Standard geometry
  # nmos_unit: gf180mcu_analog_std_lib.devices.nmos_unit_L0p5    # Longer channel
  # nmos_unit: sky130_analog_std_lib.devices.nmos_unit_std       # Different PDK
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
  gf180mcu_analog_std_lib: /shared/pdks/gf180mcu_analog_std_lib
  sky130_analog_std_lib: /shared/pdks/sky130_analog_std_lib
  analog_ip: ./libs/analog_ip
  my_project_ip: ./design/ip_blocks
```

### **Import Resolution**
```yaml
# Two supported formats:
imports:
  # Single-module file (library.module)
  amp1: analog_ip.simple_opamp
  # → analog_ip/simple_opamp.asdl (single module in file)
  
  # Multi-module file (library.file.module)
  nmos: gf180mcu_analog_std_lib.devices.nmos_unit_L0p28
  # → gf180mcu_analog_std_lib/devices.asdl, extract module 'nmos_unit_L0p28'
```

### **Multi-Module File Support**
ASDL already supports multiple modules per file through existing data structures:
- ✅ **No parser changes needed** - `modules:` section already exists
- ✅ **Simple import resolution** - just extract specific module from file
- ✅ **Library organization** - group related devices/circuits in single file
- ✅ **Backward compatibility** - both single and multi-module files supported

```yaml
# Example: analog_ip/amplifiers.asdl
modules:
  two_stage_miller: {...}
  folded_cascode: {...}
  telescopic: {...}
  
# Usage:
imports:
  ota: analog_ip.amplifiers.two_stage_miller
```

## Implementation Strategy

### **Phase 1 (MVP)**
- Implement explicit import mapping syntax
- Support unit device abstraction with multipliers
- Basic PDK primitive and design cell imports

### **Phase 2**
- Add unit device libraries for common PDKs
- Tooling for automatic unit device characterization
- Advanced import features (aliasing, versioning)

### **Deferred Complexity**
- Workspace-level library management
- Complex resolution order rules
- Multi-PDK support

## Advanced Usage: Parameterized Imports

### **Simulation Sweeps and Design Exploration**

**Parameterized Import Syntax:**
```yaml
parameters:
  device_variant: nmos_unit_L0p28  # Default
  ota_impl: two_stage_miller      # Default

imports:
  nmos_unit: gf180mcu_analog_std_lib.devices.${device_variant}
  opamp: analog_ip.amplifiers.${ota_impl}

instances:
  M1: {model: nmos_unit, params: {m: 2}}
  AMP: {model: opamp, ...}
```

### **Device Variant Sweeps**
```yaml
# Testbench can sweep device types
testbench_parameters:
  device_variants:
    - devices.nmos_unit_L0p28    # Short channel, fast
    - devices.nmos_unit_L0p5     # Long channel, matched
    - devices.nmos_unit_L1p0     # Very long, low noise

# Each simulation run uses different device variant
sweep:
  parameter: device_variant
  values: ${device_variants}  # Expands to gf180mcu_analog_std_lib.{variant}
```

### **Implementation Comparison**
```yaml
# Compare different OTA implementations in same LDO
testbench_parameters:
  ota_implementations:
    - analog_ip.amplifiers.two_stage_miller       # Standard design
    - analog_ip.amplifiers.folded_cascode         # High gain option
    - analog_ip.extracted.two_stage_extracted     # Post-layout netlist
    - analog_ip.behavioral.ota_model              # Fast simulation

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
  opamp: analog_ip.behavioral.${ota_impl}
  
  # Phase 2: Detailed schematic simulation  
  # opamp: analog_ip.amplifiers.${ota_impl}
  
  # Phase 3: Post-layout verification
  # opamp: analog_ip.extracted.${ota_impl}
```

### **Cross-PDK Comparison**
```yaml
parameters:
  pdk_variant: gf180mcu  # Default

imports:
  nmos_unit: ${pdk_variant}_analog_std_lib.devices.nmos_unit_std
  pmos_unit: ${pdk_variant}_analog_std_lib.devices.pmos_unit_std

# Compare same design across PDKs
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

## Open Questions for Implementation

### **1. Corner Management Integration**
How should testbench-level corner control integrate with the import system?
```yaml
# Testbench controls corners, but how does this interact with imports?
type: testbench
includes:
  - ldo_design.asdl
corners:
  gf180mcu: {mos: ff, bjt: typical}  # Corner specification
# Does this override any corner settings in imported designs?
# How do parameterized imports interact with corner control?
```

### **2. Namespace Resolution Rules**
What are the specific rules for local vs qualified imports?
```yaml
# Within same library - are unqualified names allowed?
# gf180mcu_analog_std_lib/nmos_unit_L0p28.asdl
imports:
  nfet_base: nfet_03v3        # Same library, unqualified?
  # vs
  nfet_base: gf180mcu.nfet_03v3  # Always qualified?

# Cross-library references - how to resolve ambiguity?
imports:
  amp: analog_ip.opamp        # Explicit
  # vs  
  amp: opamp                  # Search order rules needed?
```

### **3. Connection to PDK Integration and SPICE Generation**
How does this import strategy connect to:
- The PDK integration PRD goals we developed
- Corner-aware SPICE netlist generation  
- Library statement emission for different import types
- Port mapping from imports to SPICE subcircuit calls

```yaml
# Implementation bridge questions:
# - How do analog_std_lib imports become SPICE subckt calls?
# - How do corner settings propagate through import chain?
# - What SPICE .lib statements are needed for each import type?
# - How does pin mapping work through the import abstraction layers?
```