# Shared Ngspice Runtime Design Decisions

This document summarizes the design decisions for integrating ngspice as a shared runtime within our Python REPL workflow, streaming results into structured HDF5/xarray datasets with stable cref mappings.

---

## 1. Process Model
- Use **libngspice** (shared library) embedded in Python, not subprocess calls.
- Treat the ngspice engine as a **singleton** per process.
- Manage simulation runs sequentially; add a job queue if concurrency is needed.
- Handle callbacks from ngspice in background threads.

---

## 2. Callbacks
- **sendChar(msg):** logging and warnings
- **sendInitData(meta):** deliver vector list, units, lengths
- **sendData(step):** stream vector values at each timestep
- **controlledExit():** clean exit handling

Callbacks push lightweight events into a Python queue; heavy work (mapping and HDF5 writes) is handled in a consumer thread.

---

## 3. Python Abstractions
- `SpiceSession`: lifecycle for shared ngspice engine (`source`, `cmd`, `reset`).
- `RunHandle`: manages a single simulation run, attaches probe map, streams results.
- `ProbeResolver`: maps ngspice vector names to stable **crefs** (circuit references).
- `H5Sink`: streaming writer to HDF5; provides `xarray.Dataset` view on read.

---

## 4. Vector ↔ Hierarchy Mapping
- Each leaf in the ASDL hierarchy tree stores:
  - **cref (stable identifier):** e.g. `top.ota1.m1.op.gm`
  - **ngspice vector name:** e.g. `@m.x_ota1.m1[gm]`
- **Alias graph:** allow multiple crefs to point to the same underlying vec.
- Resolver stored in `probe_map.json`.

Example:
```yaml
map:
  top.ota1.nodes.out.v: "v(out)"
  top.ota1.m1.op.gm:    "@m.x_ota1.m1[gm]"
aliases:
  top.ota1.vout:        "top.ota1.nodes.out.v"
```

---

## 5. HDF5/xarray Layout
- Append-only, chunked layout for long runs and Monte Carlo.
- **Structure:**
  ```
  /runs/<run_id>/
    attrs: metadata (analysis, seeds, corners, netlist hash, etc.)
    inputs/
      netlist, params.yaml, probe_map.json, tree.json
    time: float64, shape=(T,), chunks=(chunk_T,)
    vectors/<cref>/data: float64, shape=(T,), chunks=(chunk_T,)
      attrs: unit, source_vec, node_kind, aliases
    logs/: ngspice.txt, warnings.jsonl
  ```
- On read: expose as `xarray.Dataset` with coords `t` and data_vars per cref.

---

## 6. Streaming & Threading
- Callbacks enqueue data events quickly.
- Python worker thread consumes queue:
  - Resolves crefs
  - Appends to HDF5 with `threading.Lock()` (h5py not thread-safe)
- End-of-run marker finalizes group (`_SUCCESS`).

---

## 7. Monte Carlo, Sweeps, Corners
- **Run ID** encodes analysis, corner, seed, sweep index, netlist hash.
- Store seeds and corner info in run attrs.
- For sweeps:
  - Either single ngspice `.step` → add `step_index` coordinate
  - Or external loop: one run per sweep point

---

## 8. Failure Handling
- Missing vectors → mark dataset with `status=missing`
- Convergence errors → `status=failed`, still save partial results
- User interrupts → stop ngspice, finalize partial run
- Memory → stream to disk, avoid large in-RAM buffers

---

## 9. REPL Ergonomics
Example usage:
```python
s = SpiceSession()
s.source_netlist(asdlc_emit(...))

run = RunHandle(s, run_id=uuid4(), probe_map=resolver, h5_sink=H5Sink("sims.h5"))
run.run_tran("1n", "10u")

ds = open_xarray("sims.h5", run_id)
ds["v_top_ota1_out"].plot()
```

- Supports `alterparam` for parameter sweeps
- Reset between netlist changes
- Measurements done in Python or ngspice `.measure`

---

## 10. API Surface for Simorc
- `SimSession` → wraps `SpiceSession`
- `SimJobSpec` → declares analysis, sweeps, corners
- `SimRun` → run metadata, status
- `ProbeResolver` → cref ↔ vector mapping
- `ResultStore` → HDF5 I/O + xarray views
- `yaml2plot` consumes cref identifiers directly

---

## Key Benefits
- Interactive REPL workflow with shared runtime.
- Stable crefs decoupled from simulator-specific names.
- Direct streaming into HDF5/xarray, simulator-agnostic dataset format.
- Efficient handling of long simulations, sweeps, and Monte Carlo.

