# ASDL Unified Architecture Demo

This example demonstrates the **unified ASDL module architecture** where primitive and hierarchical modules coexist in a single, clean design flow.

## Files

- **`unified_architecture_demo.asdl`** - Source ASDL design showcasing both primitive and hierarchical modules
- **`unified_architecture_demo.spice`** - Generated SPICE netlist demonstrating the unified compilation
- **`compile_demo.py`** - Compilation script that parses ASDL and generates SPICE
- **`unified_architecture_README.md`** - This documentation file

## Architecture Overview

### Primitive Modules (with `spice_template`)
**Generate inline SPICE** - no subcircuit overhead for basic devices

```yaml
nfet_03v3:
  ports: {D: {dir: in_out}, G: {dir: in}, S: {dir: in_out}, B: {dir: in_out}}
  parameters: {L: "0.28u", W: "3u", M: 1}
  spice_template: "MN{name} {D} {G} {S} {B} nfet_03v3 L={L} W={W} m={M}"
  pdk: "gf180mcu"  # Drives automatic .include generation
```

**Result**: Direct SPICE device lines within hierarchical modules
```spice
MNMN out in vss vss nfet_03v3 L=0.28u W=3u m=1
```

### Hierarchical Modules (with `instances`)
**Generate `.subckt` definitions** - proper subcircuits for circuit blocks

```yaml
inverter:
  ports: {in: {dir: in}, out: {dir: out}, vdd: {dir: in}, vss: {dir: in}}
  instances:
    MN: {model: nfet_03v3, mappings: {D: out, G: in, S: vss, B: vss}}
    MP: {model: pfet_03v3, mappings: {D: out, G: in, S: vdd, B: vdd}}
```

**Result**: Subcircuit definition with inline primitives
```spice
.subckt inverter in out vdd vss
  MNMN out in vss vss nfet_03v3 L=0.28u W=3u m=1
  MPMP out in vdd vdd pfet_03v3 L=0.28u W=6u m=2
.ends
```

## Design Hierarchy

The demo includes a **four-level hierarchy** showing the architecture's flexibility:

### Level 1: PDK Primitives
- **`nfet_03v3`**, **`pfet_03v3`** - GF180MCU transistors with PDK includes
- **`resistor`**, **`capacitor`** - SPICE built-in primitives

### Level 2: Basic Circuits  
- **`inverter`** - CMOS inverter using transistor primitives
- **`rc_filter`** - RC low-pass filter using SPICE primitives
- **`current_mirror`** - NMOS current mirror with 1:2:4 ratios

### Level 3: Complex Circuits
- **`two_stage_buffer`** - Combines inverters and RC filter with parameterization

### Level 4: Top-Level Integration
- **Main circuit instantiation** - `XMAIN in out vdd vss two_stage_buffer`

## Key Features Demonstrated

### 🔧 **Automatic PDK Integration**
```spice
* PDK model includes
.include "gf180mcu_fd_pr/models/ngspice/design.ngspice"
```

### 🏗️ **Efficient SPICE Generation**
- **Primitives**: Generate inline (no subcircuit overhead)
- **Hierarchical**: Generate proper `.subckt` definitions
- **No unnecessary wrapper subcircuits** for simple devices

### 📐 **Rich Parameter Substitution**
```yaml
# Module defaults + instance overrides
parameters: {L: "0.28u", W: "3u", M: 1}  # Defaults
instances:
  MN: {parameters: {M: 2, W: "4u"}}      # Overrides: M=2, W=4u, L=0.28u (default)
```

### 🔗 **Hierarchical Module Composition**  
```yaml
two_stage_buffer:
  instances:
    INV1: {model: inverter, parameters: {nmos_M: 1, pmos_M: 2}}
    FILTER: {model: rc_filter, parameters: {R_val: "5k", C_val: "50p"}}
    INV2: {model: inverter, parameters: {nmos_M: 2, pmos_M: 4}}
```

## Compilation Results

### Statistics
- **📄 Total lines**: 53 SPICE lines generated
- **📦 PDK includes**: 1 automatic include for gf180mcu 
- **🏗️ Subcircuits**: 4 hierarchical modules → `.subckt` definitions
- **🔧 Device instances**: 11 total (8 inline primitives + 3 subcircuit calls)

### Generated Structure
```spice
* PDK includes (automatic from pdk field)
.include "gf180mcu_fd_pr/models/ngspice/design.ngspice"

* Hierarchical subcircuits only (primitives are inline)
.subckt inverter in out vdd vss
  MNMN out in vss vss nfet_03v3 L=0.28u W=3u m={nmos_M}  # Inline primitive
  MPMP out in vdd vdd pfet_03v3 L=0.28u W=6u m={pmos_M}  # Inline primitive
.ends

.subckt rc_filter in out gnd
  RR1 in out {R_val} TC1=0 TC2=0  # Inline SPICE primitive
  CC1 out gnd {C_val}             # Inline SPICE primitive  
.ends

.subckt current_mirror iref iout1 iout2 vss
  MNM_REF iref iref vss vss nfet_03v3 L=0.28u W=3u m=1   # Inline primitive
  MNM_OUT1 iout1 iref vss vss nfet_03v3 L=0.28u W=3u m=2 # Inline primitive
  MNM_OUT2 iout2 iref vss vss nfet_03v3 L=0.28u W=3u m=4 # Inline primitive
.ends

.subckt two_stage_buffer in out vdd vss
  X_INV1 in stage1_out vdd vss inverter ...     # Hierarchical call
  X_FILTER stage1_out filtered_out vss rc_filter ...  # Hierarchical call
  X_INV2 filtered_out out vdd vss inverter ...  # Hierarchical call
.ends

* Main instantiation
XMAIN in out vdd vss two_stage_buffer
```

## Usage

### Compile the Example
```bash
# From ASDL root directory
python examples/compile_demo.py
```

### Use in SPICE Simulator
```bash
# The generated SPICE file can be used directly
ngspice unified_architecture_demo.spice
```

## Benefits of Unified Architecture

### 🎯 **Clean Separation of Concerns**
- **Primitive modules**: Focus on device-level parameters and PDK integration
- **Hierarchical modules**: Focus on circuit topology and design intent

### ⚡ **Efficient SPICE Output**
- **No subcircuit overhead** for primitive devices (direct inline generation)
- **Proper hierarchical structure** for complex circuits (`.subckt` definitions)

### 🔧 **Technology Independence**
- **Same design logic** works across different PDKs
- **Only primitive modules change** when switching technologies
- **Automatic includes** for technology-specific model files

### 📐 **Flexible Parameterization**
- **Module-level defaults** with **instance-level overrides**
- **Template-based substitution** with `{parameter}` placeholders
- **Rich parameter expression** support

### 🏗️ **Scalable Design Flow**
- **Composable hierarchy** - modules can contain other modules
- **Reusable IP blocks** - same modules used in multiple designs  
- **Clear design intent** - topology separated from technology details

This unified architecture provides the foundation for the **ASDL import system**, where designs can reference modules from different files and libraries while maintaining the same clean primitive vs. hierarchical distinction.