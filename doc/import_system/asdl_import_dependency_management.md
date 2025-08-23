# ASDL Import Abstraction Strategy Summary

## Core Philosophy
**Complete separation of design logic from physical implementation through explicit import mapping**

- ASDL imports are **purely logical references** to `.asdl` files on disk.  
- ASDL does **not** manage versioning or reproducibility.  
- Versioning, checksums, and vendoring are handled by external tools such as **`ams-compose`**.  
- Imports always resolve through a configured **search path** (`ASDL_PATH`, `asdl.config.yaml`, or CLI).

---

## Unified Import Mechanism

### **Single Import Syntax for All Dependencies**
```yaml
imports:
  file_alias: library_dir/file_name.asdl
```

### **Three Dependency Types, One Syntax**
```yaml
imports:
  # PDK primitive files
  pdk_primitives: gf180mcu_pdk/primitives.asdl
  
  # Design IP files  
  amplifiers: analog_ip/amplifiers.asdl
  
  # SPICE primitive libraries (always implicit)
  # analoglib: analoglib  # Implicit - always available
```

### **Module References with Qualified Names**
```yaml
instances:
  M1:  {model: pdk_primitives.nfet_03v3}        # PDK primitive module
  AMP: {model: amplifiers.two_stage_miller}     # Design IP module
  VDC: {model: analoglib.vdc}                   # SPICE primitive
```

---

## Local Shorthand: `model_alias`

Designs often need concise names for imported modules. To improve readability and IP portability, ASDL supports a **`model_alias`** section.

```yaml
imports: 
  std_devices: gf180mcu_std_tiles/devices.asdl 

model_alias: 
  nmos_unit: std_devices.nmos_unit_short 

modules: 
  current_mirror: 
    instances:
      M_REF:  {model: nmos_unit, parameters: {M: 1}}  # Reference
      M_OUT1: {model: nmos_unit, parameters: {M: 2}}  # 2x current
      M_OUT2: {model: nmos_unit, parameters: {M: 4}}  # 4x current
```

### Rules for `model_alias`
- Aliases are **file-local only**; they do not propagate when this file is imported.  
- Resolution order:  
  1. Local module definitions  
  2. `model_alias` bindings  
  3. Imported modules via `imports`  
- Lint rules:  
  - Error if alias collides with an import name.  
  - Error if alias refers to a non-existent module.  
  - Warning if alias is declared but unused.

---

## Unit Device Abstraction

### **Three-Layer Architecture**

**Layer 1: PDK Primitives** (raw SPICE device models)
```yaml
modules:
  nfet_03v3:
    ports: [D, G, S, B]
    parameters: {L: 0.28u, W: 3u, NF: 2, M: 1}
    spice_template: MN {D} {G} {S} {B} nfet_03v3 L={L} W={W} nf={NF} m={M}
    pdk: gf180mcu
```

**Layer 2: Unit Devices** (standardized device tiles with fixed geometry, multiplier-only interface)
```yaml
modules:
  nmos_unit_short:
    ports: [D, G, S, B]
    parameters: {M: 1}
    variables: {L: 0.28u, W: 3u, NF: 2}
    spice_template: MN{name} {D} {G} {S} {B} nfet_03v3 L={L} W={W} nf={NF} m={M}
    pdk: gf180mcu
```

**Layer 3: Design Logic** (technology-independent, multiplier-only)
```yaml
imports:
  std_devices: gf180mcu_std_tiles/devices.asdl

model_alias:
  nmos_unit: std_devices.nmos_unit_short

modules:
  current_mirror:
    instances:
      M_REF:  {model: nmos_unit, parameters: {M: 1}}  
      M_OUT1: {model: nmos_unit, parameters: {M: 2}}  
      M_OUT2: {model: nmos_unit, parameters: {M: 4}}
```

---

## File Discovery & Resolution

### **ASDL_PATH environment variable**
- Works like `PATH`.  
- Colon-separated list of directories (on POSIX; `;` on Windows).  
- Compiler searches these roots in order.

```bash
# Example (POSIX)
export ASDL_PATH="/pdks:/workspace/third_party:./libs"
```

### **Resolution order (first match wins)**
1. CLI: `--search-path` args  
2. Config: `asdl.config.yaml` search_paths  
3. Environment: `ASDL_PATH`  
4. Built-ins (optional): `./`, `./libs`, `./third_party`

### **Example Resolution**
```yaml
imports:
  std_devices: gf180mcu_std_tiles/devices.asdl
```
With:
```
ASDL_PATH=/pdks:/workspace/third_party
```
Probes:
```
/pdks/gf180mcu_std_tiles/devices.asdl
/workspace/third_party/gf180mcu_std_tiles/devices.asdl
```

### **Lint rules**
- E001: Import path does not end with `.asdl`  
- E002: Import not found in any search root (print probe list)  
- E003: Alias collides with import name  
- E004: model not found in referenced file  

---

## Key Benefits

1. **Technology Independence**  
   - Same design works across PDKs — only imports/aliases change.

2. **Design Exploration Flexibility**  
   - Swap implementations with a one-line alias change.

3. **Clear Design Intent**  
   - Multiplier ratios show intent directly.  
   - Matching requirements explicit via identical multipliers.

4. **Clean Dependency Management**  
   - Imports = file-level dependencies.  
   - Aliases = file-local shorthands.  
   - No hidden versioning logic inside ASDL.

5. **LVS Compatibility**  
   - Unit devices as primitives generate inline SPICE (no subcircuits).  
   - No `.param` statements that break LVS tools.

---

## Implementation Strategy

### **Phase 1 (MVP)**
- Explicit `.asdl` file imports  
- `model_alias` section  
- Unit device abstraction with multipliers  
- Deterministic file discovery with `ASDL_PATH`

### **Phase 2**
- Add unit device libraries for common PDKs  
- Tooling for auto-characterization  
- Linter and diagnostics

### **Deferred Complexity**
- Behavioral model fallbacks  
- Multi-PDK meta-parameters  
- Advanced provenance stamping

---

## Result
**Analog designs become topology-focused like digital designs**, with physical implementation abstracted into reusable unit device libraries.  

Design files stay clean, portable, and reproducible.  
**ASDL handles imports, aliases, and resolution. `ams-compose` handles versions and reproducibility.**
