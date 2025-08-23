
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
