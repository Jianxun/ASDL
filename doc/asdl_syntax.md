# YAML Analog Structured Description Language (ASDL) Cheat‑Sheet

This file documents the **compact YAML dialect** we just used to describe analog circuits.  It is meant to be read side‑by‑side with the example OTA netlist so you can create, review, or auto‑generate new designs quickly.

---

## 1. File‐Level Layout

```yaml
.defaults: &DEF   # global anchors (section §4)
modules:          # list of reusable sub‑circuits (§2)
  diff_pair: …
  current_mirror: …
  …
```

*Only two top keys are mandatory*: `*.defaults` (optional but recommended) and `modules`.

---

## 2. Module Block

```yaml
<name>:
  nets: {<net_name>: <role>, …}
  parameters: {<key>: <value>|{…}}
  circuits: [ <device‑1>, <device‑2>, … ]
```

| Field        | Purpose                                                    |
| ------------ | ---------------------------------------------------------- |
| `nets`       | Declares the external interface. `role` abbreviations → §3 |
| `parameters` | Design‑time knobs. Scalars or nested maps are allowed.     |
| `circuits`   | List of **devices or sub‑module instances** (see §5).      |

> **Tip:** You can nest modules indefinitely—great for hierarchy.

---

## 3. Net Roles (1‑letter shorthands)

| Abbrev | Expands to          | Used for                  |
| ------ | ------------------- | ------------------------- |
| `in`   | `pin: input`        | signal source             |
| `out`  | `pin: output`       | signal sink               |
| `io`   | `pin: input_output` | bidirectional / bias node |
| `pwr`  | `pin: power`        | positive supply           |
| `gnd`  | `pin: ground`       | ground or negative supply |

The netlist generator maps these to whatever syntax your Spice flavour expects (e.g. `.SUBCKT` pin order or explicit directives).

---

## 4. Anchors & Aliases

```yaml
.defaults: &NMOS {model: nmos_unit, B: GND}
```

*YAML anchors* (`&NMOS`) let you **factor out boiler‑plate**.  Later devices reuse it via `<<: *NMOS`, then override only what differs:

```yaml
- {<<: *NMOS, name: MN1, D: out, S: gnd, G: in, multi: 4}
```

---

## 5. Device / Instance Object

```yaml
{<<: *PMOS, name: MP_drv, S: VDD, D: out, G: n1, multi: ${M.drv}}
```

| Key      | Meaning                                                      |
| -------- | ------------------------------------------------------------ |
| `<<`     | YAML *merge key*: pulls in anchor content                    |
| `name`   | Unique Spice instance name (optional)                        |
| `model`  | Primitive or sub‑module name (comes from anchor or explicit) |
| Pin keys | `S:`, `D:`, `G:` … map to net names                          |
| Others   | Arbitrary parameters (e.g. `multi`, `L`, `W`, `value`)       |

### Arrays for symmetry

Write a list to describe many similar devices:

```yaml
- {<<: *NMOS, name: MN_[P,N], S: tail, …}
```

Generators expand the pseudo‑name `MN_[P,N]` into two instances `MN_P`, `MN_N`.

---

## 6. Parameter Substitution `${…}`

*Curly‑dollar* entries are **templated expressions** resolved **before** Spice generation.

```yaml
multi: ${M.diff}         # pulls value from current parameters map
value: ${Cc}             # capacitor sizing
```

You can embed simple math if the pre‑processor supports it—e.g. `${M.diff * 2}`.

---

## 7. Example: Mini‑Module

```yaml
modules:
  bias_source:
    nets: {out: out, VDD: pwr, GND: gnd}
    parameters: {Iref: 10u}
    circuits:
      - {<<: *PMOS, name: MP_bias, D: out, S: VDD, G: out, multi: 1}
      - {model: resistor_unit, name: Rset,
         nodes: [out, GND], value: ${VDD / Iref}}
```

---

## 8. Generator Workflow

1. **Parse YAML** → build an in‑memory graph.
2. **Resolve** anchors, arrays, and `${}` expressions.
3. **Emit** canonical Spice/SKiDL/Verilog‑AMS.

Because the YAML is *declarative*, you can trivially iterate over corners or sweep any parameter set by re‑loading with a different `parameters` map.

---

## 9. Best Practices Checklist

* [ ] Place all numeric sizing in the `parameters` block—*no hard numbers* in pin lists.
* [ ] Use anchors for every primitive device type.
* [ ] Keep net names short; only export what higher levels need.
* [ ] Version modules: `diff_pair_v2:` if you spin the topology but need to keep v1 alive.
* [ ] Treat this YAML as *source code*: commit, diff, review.
