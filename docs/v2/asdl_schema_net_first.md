# Tier-1 ASDL — Draft Schema v0.3 (authoring surface)

This describes the **Tier-1 authoring YAML shape** (not the Tier-2 normalized IR).
Tier-1 supports **modules** (structural topology) + **devices** (leaf emitters), plus optional `top`.

---

## 0) Document Root

```yaml
top: <module_name>            # optional; required if multiple modules exist

modules:                      # optional if you only author leaf devices, but usually present
  <module_name>: <ModuleDef>

devices:                      # optional
  <device_name>: <DeviceDef>
```

Rules:
- If `top` is absent:
  - If exactly 1 module exists → that module is the implicit top.
  - Else → error (ambiguous entry point).
- Names (`<module_name>`, `<device_name>`, instance names, net names) are strings with existing naming rules.
- Name collision rule (recommended):
  - A name must not appear in both `modules` and `devices` (unless namespaces are later introduced).

---

## 1) ModuleDef (structural / topology)

```yaml
modules:
  ota:
    instances: <InstancesBlock>
    nets: <NetsBlock>

    exports: <ExportsBlock>   # optional; port propagation sugar

    # comments/docstrings/groups are supported as YAML comments (see §6)
```

### 1.1 InstancesBlock

Two equivalent styles are allowed:

#### Style A — flat map
```yaml
instances:
  MN_IN<P,N>: nfet_3p3 m=8 (B:$VSS)
  MP_LOAD<P,N>: pfet_3p3 m=2 (B:$VDD)
  MTAIL: nfet_3p3 m=4 (B:$VSS)
```

#### Style B — suffix block sugar (optional)
```yaml
instances:
  suffix <P,N>:
    MN_IN: nfet_3p3 m=8 (B:$VSS)
    MP_LOAD: pfet_3p3 m=2 (B:$VDD)
  MTAIL: nfet_3p3 m=4 (B:$VSS)
```

Semantics (lowering):
- `suffix <P,N>:` applies the literal domain `<P,N>` to each instance name in the block:
  - `MN_IN` becomes `MN_IN<P,N>` (i.e., expands to `MN_INP`, `MN_INN`).
- Parameters after the type token are **instance-params** (inline grammar); Tier-1 treats them as opaque strings until Tier-2.
- Optional **inline pin-bindings** `(Pin:Net ...)` are allowed:
  - They create explicit connectivity equivalent to writing those endpoints in `nets:`.
  - Conflicts with `nets:` are errors (see §1.2).

InstanceDecl shape:
```yaml
<InstanceName>: <TypeName> <ParamTokens...> ( <PinBind>... )?
```

PinBind shape:
```yaml
<PIN>: <NET>
```

Notes:
- `<TypeName>` resolves to either:
  - a `device` (leaf emitter), OR
  - another `module` (hierarchical instance)
- Inline pin-bindings are recommended for bulk-ish per-instance ties (e.g., bulks):
  - `M1: nmos_unit m=2 (B:$VSS)`

---

### 1.2 NetsBlock

```yaml
nets:
  VFOLD<P,N>: MP_FOLD<P,N>.D MN_IN<P,N>.D
  $VIN<P,N>: MN_IN<P,N>.G
  VTAIL: MN_IN<P,N>.S
  $VDD: MP_FOLD*.S MP_STG2*.S
  $VSS: MN_CS*.S MN_STG2*.S MTAIL.S
```

NetDecl shape:
```yaml
<NetName>: <EndpointToken> <EndpointToken> ...
```

Rules:
- Endpoint list is **whitespace-separated** (no commas).
- `nets:` contains topology only (no arithmetic).
- `$` on the net name marks **export** (module port).
  - **Option B ports:** A module’s port list is the set of `$...` nets in that module.
  - **Port order** is the appearance order of `$...` nets in this module’s `nets:` mapping.
  - Inline pin-bindings do **not** create exported ports; `$...` nets must appear in `nets:`.
- Expansion markers supported in net names and endpoint instance names:
  - Literal domain: `<A,B,...>`
  - Numeric domain: `[7:0]` or `[0..7]`
  - All-suffix marker: `*` (see broadcasting rules below)

Endpoint grammar (Tier-1 surface):
- `Inst.Pin`
- `Inst*.Pin`
- `Inst<P,N>.Pin`
- `Inst<N,P>.Pin`
- `Inst[7:0].Pin`

#### `*` semantics (two-mode)

**Mode 1 — LHS is a single net (broadcast net):**
- If LHS has **no domain** (no `<...>` or `[...]`), then the net is a *broadcast collector*:
  - RHS endpoint tokens may have mismatched domains.
  - Example:
    ```yaml
    VSS: M1.S M2*.S M3*.S
    ```
  - Interpretation:
    - `M1.S` is a single endpoint.
    - `M2*.S` and `M3*.S` expand using inferred domains from their own context (Tier-2 deterministic expansion rules).
    - All resulting endpoints connect to the single net `VSS`.

**Mode 2 — LHS has a domain (zipped expansion):**
- If LHS includes a domain (e.g. `$VIN<P,N>` or `BUS[7:0]`), then `*` is only valid when:
  - every `*` in that NetDecl can be inferred to the **exact same domain**, and
  - every RHS token expands to the same cardinality as the LHS domain
  - expansion is **zip-aligned** by index.
- Otherwise → error.
Note: LHS net names **must not** use `*` as a domain placeholder. Use explicit `<...>` or `[...]` on LHS.

(Exact deterministic expansion rules are defined separately and reused here.)

#### Connectivity precedence and conflicts
- `nets:` and inline instance pin-bindings both create explicit connectivity.
- If the same endpoint is bound to two different nets → error.
- Redundant bindings to the same net are permitted (may warn under strict lint).

---

### 1.3 ExportsBlock (optional) — port propagation / re-export

Purpose:
- Reduce port boilerplate when building hierarchy (especially large digital control buses).
- `exports:` only forwards **exported child ports** (hard contract).

Shape:
```yaml
exports:
  <InstName>: [ <Pattern>, <Pattern>, ... ]
```

Example:
```yaml
exports:
  U_CTRL: [CTRL_*, SPI_*, -SPI_DBG_*]
  U_PLL:  [*]
```

Pattern grammar:
- Glob patterns over child **exported port names** with `*` wildcard only.
- Negation supported via leading `-`.
- `$` prefix in patterns is **optional**.
- Matching is done on the **logical port name** (i.e., after stripping a leading `$` from the child exported name).

Semantics (lowering):
1. `<InstName>` must resolve to a **module instance** (not a device).
2. Compute the ordered child export list:
   - child exports are nets in the child module whose net name starts with `$`
   - order is the appearance order in the child `nets:` mapping
3. Apply patterns:
   - union of all positive matches
   - then remove all negated matches
   - preserve child export order
4. For each selected child port `P`:
   - parent exports `P`
   - parent connects `$P` to `<InstName>.P`

Equivalent lowering form:
```yaml
nets:
  $P: <InstName>.P
```

Constraints / Errors:
- **Forward exported ports only:** forwarding can only target child ports derived from `$...` nets.
- **No renaming in exports:** to rename, author explicitly in `nets:`:
  ```yaml
  nets:
    $SYS_SPI_MOSI: U_CTRL.SPI_MOSI
  ```
- **No arrayed instance forwarding:** `<InstName>` must be a single, non-expanded instance name.
  - If `<InstName>` contains `<...>`, `[...]`, or `*` → error (would collide without renaming).
- If the parent already explicitly defines `$P` in `nets:` → error (avoid hidden collisions).
- If two `exports:` entries would produce the same parent port name → error.
- If a positive pattern matches zero child ports → warning (optionally error in strict lint).

Port order on the parent:
- Parent port list is ordered as:
  1) explicit `$...` nets in `nets:` (source order)
  2) forwarded ports in `exports:` (file order of `exports:` keys, and within each, child export order)

---

## 2) DeviceDef (leaf emitter, template-based)

```yaml
devices:
  nfet_3p3:
    ports: [D, G, S, B]
    params:
      L: 0.5u
      W: 5u
      NF: 1
      m: 1

    backends:
      sim.ngspice:
        model: nfet_03v3
        template: 'X{inst} {D} {G} {S} {B} {model} L={L} W={W} NF={NF} m={m}'

      sim.spectre:
        model: nmos_03v3
        template: 'M{inst} ({D} {G} {S} {B}) {model} l={L} w={W} m={m}'

  res:
    ports: [P, N]
    params:
      value: 1k
    backends:
      sim.ngspice:
        template: 'R{inst} {P} {N} {value}'
      sim.spectre:
        template: 'R{inst} ({P} {N}) {value}'
      lvs.klayout:
        template: 'R{inst} {P} {N} {value}'
```

Rules:
- `ports` is an **ordered list**; no separate `port_order`.
- `params` is a simple map of default values (all params have defaults).
  - Instance decls may override these defaults (Tier-2 parses/validates overrides).
- `backends.<key>` is an overlay:
  - any fields defined under a backend entry are available as `{placeholders}` in the `template`
  - backend entry may override shared `params` (deep-merge) if needed
- `{inst}` is always provided by the emitter.
- Unknown placeholders in a template are an error at Tier-2 / emission time.

Notes:
- “subckt_ref” is represented naturally as a device whose template emits an `X... {model}` call.
- Includes/deck binding is expected to be handled by compile environment (not required in Tier-1).

---

## 3) Entry point

```yaml
top: <module_name>
```

- Optional only when exactly one module exists.

---

## 4) Flatten vs Subckt emission (not schema; backend option)

Tier-1 does not encode “flat authoring”.
Backends choose:
- `emit.top_mode: flat` (quick sim TB)
- `emit.top_mode: subckt` (LVS)

---

## 5) Aliases (deferred)

Alias semantics are deferred in v0.3.
If the author needs semantic reminders (e.g., two names for one node), use YAML comments.

---

## 6) Comments / Docstrings / Group annotations (lexical)

Comments are YAML comments and are **non-semantic** for connectivity.
Recommended conventions:
- Item docstring: contiguous comment block immediately preceding a net/instance/device attaches to that item.
- Group comments (optional convention):
  - `#@group <text>` begins a group
  - `#@end` ends a group
  - group applies to consecutive items in the same mapping

(Exact attachment semantics can be specified separately; schema-wise they remain comments.)
