# ASDL Simulation Session & CRef Design Decisions

This document summarizes the design decisions we made about the **canonical circuit reference (CRef)** system and the **simulation orchestration session** for `simorc`.

---

## 1. Modules vs Instances

- **ModuleDef (definition)**:  
  - Template/type from ASDL source.  
  - Contains ports, nets, sub-instance templates, parameter defaults, documentation.  
  - Has *capabilities* flags:
    - `kind`: "primitive" or "composite"
    - `device_kind` (MOS, RES, CAP…)
    - `terminal_set` (valid terminals for primitives)
    - `has_op_params`, `has_branch_currents`
  - Lives in a **ModuleLibrary** (`s.lib`).

- **Instance (embodiment)**:  
  - A concrete node in the design tree.  
  - Has an `instance name` (ota1, ota2, …) and `path` (`top.ldo.ota1`).  
  - References its definition (`module: ModuleDef`).  
  - Carries resolved parameters.  
  - Holds child **instances** and **nets** (including ports).  
  - All **CRef sugars** (`.v()`, `.i()`, `.op()`, …) live here.  
  - Capabilities are checked via the linked `ModuleDef`.

**Tree structure**: `s.tree` is the **Instance tree** (strict tree).  
Definitions live separately in `s.lib`.

---

## 2. CRef (Canonical Reference) API

- **On Instance Ports (all modules)**:
  - `.v(port)` → waveform voltage at a port.  
  - `.vdc(port)` (≡ `.op('vdc:port')`) → DC operating point voltage at a port.  

- **On Primitive Instances** (gated by `ModuleDef.capabilities`):
  - `.i(term)` → waveform branch current at a terminal.  
  - `.idc(term)` (≡ `.op('idc:term')`) → DC branch current at a terminal.  
  - `.op(name)` → operating-point scalars (gm, ro, …).  

- **Sugars for MOS-like devices**:
  - `.vgs()`, `.vds()`, etc.

- **Errors**:
  - `OpNotSupportedError` when calling `.op()` on composites.  
  - `InvalidTerminalError` when asking for non-existent terminals.

---

## 3. Proxies

- **VectorProxy**:  
  - Represents a waveform (voltage/current).  
  - Fields: `cref`, `kind`, `sim_name` (bound lazily), `save()`.  

- **ScalarProxy**:  
  - Represents OP/param scalars.  
  - Fields: `cref`, `kind`, `save()`.  

- **VectorExpr**:  
  - Symbolic algebra (`diff`, `add`, etc.) over proxies.

- **Handles/Aliases**:  
  - You can assign proxies to Python variables:  
    ```python
    vout = s.tree.top.ota1.v('out').save()
    plot(vout)
    ```

---

## 4. Simulation Orchestration (Session)

- **Session object (`s`)**:
  - `asdl_path`: entry ASDL file.  
  - `lib`: `ModuleLibrary` of all `ModuleDef`.  
  - `tree`: elaborated `Instance` tree.  
  - `vars`: dict of tunable parameters/knobs.  
  - `adapter`: simulator binding (ngspice adapter first).  
  - `store`: results backend (`RawfileStore` or `SharedSpiceStore`).  
  - `sim`: registry of analyses (AC, TRAN, DC, …).  
  - `save_plan`: queued proxies to save.  
  - `results`: dict of datasets per analysis.  
  - `alias`: namespace for user aliases.

- **Lifecycle**:
  - `s.netlist()`:
    - Runs compiler, populates `s.lib` and `s.tree`.  
    - Populates `s.vars` with defaults.  
    - Invalidates cached sim bindings.  
  - `s.sim.register("ac")`: load an analysis module.  
  - `s.sim.ac.init()/run()/post()` or simply `s.sim.ac()`.  
  - Results available in `s.results["ac"]`.

---

## 5. Data Model

- **Hierarchy**:  
  - Strict tree of **Instances**; each points to a **ModuleDef**.  
  - `s.tree` is discoverable (children via `.instances`, `.nets`, `.ports`).  
  - Attribute sugar: `ota1.m1.op("gm")`, `ota1.out.v()`.

- **CRefs**:  
  - Always canonical string paths (`top.ota1.m1.op("gm")`).  
  - Stored in datasets as keys.  
  - Aliases in Python for reuse, but canonical CRefs in logs/artifacts.

- **Results**:  
  - `xarray.Dataset` keyed by CRefs (waveforms).  
  - Companion `ds_op` for scalars.  
  - Backend-agnostic (rawfile or shared lib).  

---

## 6. Workflow Example

```python
s = Session('top.asdl')
s.netlist()

s.sim.register('ac')
s.sim.register('tran')

s.vars['c_load'] = 1e-12
s.sim.ac()

vout = s.tree.top.ota1.v('out').save()
s.plot(vout)

# edit ota.asdl externally
s.netlist()
s.sim.ac()
s.plot(vout)   # same handle still valid
```

---

## 7. Design Principles

- **Modules define, Instances do.**
- **Strict tree**: always hierarchical, no DAG in public API.  
- **CRef sugars**: methods, not properties → no namespace collisions.  
- **Discoverable API**: dict-like collections, attribute access, typed methods.  
- **Backend-agnostic**: rawfile or shared lib, same dataset API.  
- **Stable identifiers**: canonical CRefs for reproducibility.  
- **Agent-friendly**: everything exposed via Python API, fully introspectable.
