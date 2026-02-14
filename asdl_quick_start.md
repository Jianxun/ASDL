# ASDL Quick Start

## What ASDL is
ASDL (Analog Structured Description Language) is a YAML-based hardware authoring format for analog circuits.

In this repo, ASDL is compiled through a deterministic pipeline:
`AST -> PatternedGraph -> AtomizedGraph -> NetlistIR -> backend netlist`.

Use ASDL to describe:
- reusable `devices`
- hierarchical `modules`
- connectivity via net-first `nets`
- optional imports from other ASDL libraries

## Authoring mental model
Write modules in this order:
1. `instances`: place blocks/devices with inline params
2. `nets`: connect endpoints (source of truth for connectivity)
3. optional `patterns`, `instance_defaults`, `exports`, `variables`

Key point: connectivity is net-first. The `nets` map is authoritative.

## Minimal ASDL example
```yaml
top: inv

modules:
  inv:
    instances:
      mn: nfet_03v3 L=0.5u W=5u
      mp: pfet_03v3 L=0.5u W=5u
    nets:
      $in: [mn.g, mp.g]
      $out: [mn.d, mp.d]
      $vss: [mn.s, mn.b]
      $vdd: [mp.s, mp.b]

devices:
  nfet_03v3:
    ports: [d, g, s, b]
    backends:
      sim.ngspice:
        template: "M{instance} {d} {g} {s} {b} {model}"
        model: nfet_03v3

  pfet_03v3:
    ports: [d, g, s, b]
    backends:
      sim.ngspice:
        template: "M{instance} {d} {g} {s} {b} {model}"
        model: pfet_03v3
```

## Basic authoring rules (high-signal)
- Names: literals must match `[A-Za-z_][A-Za-z0-9_]*`.
- Reserved delimiters in literal names are forbidden: `< > | : ;`.
- At least one of `modules` or `devices` must exist.
- If more than one module exists, `top` is required.
- `instances` values are raw inline strings, e.g. `my_device w=1u l=0.18u`.
- `nets` values must be lists of endpoint strings.
- Prefix a net with `$` to expose it as a module port.
- Port order is deterministic: `$` nets in declaration order, then forwarded exports.
- Device `backends` must be non-empty.
- Each backend entry must include a string `template`.

## Patterns you can use
ASDL supports pattern tokens that are preserved in AST and expanded later:
- enum: `<P|N>`
- range: `<7:0>`
- named pattern reference: `<@BUS>`
- wildcard: `*`

Patterns commonly appear in instance names, net names, and endpoint tokens.

## Imports and qualified refs
Use `imports` at top level to bring in external ASDL files:
```yaml
imports:
  gf: gf180mcu.asdl
```

Then reference imported symbols in instances via `namespace.symbol`:
```yaml
instances:
  m1: gf.nfet_03v3 w=1u l=0.5u
```

## Variables
`variables` are module-local constants used in inline instance parameter values via `{var}` placeholders.

Example:
```yaml
variables:
  VDD: 3.3
instances:
  vsrc: vdc dc={VDD}
```

## .asdlrc project config (optional)
ASDL can load a nearby `.asdlrc`:
- `schema_version: 1` (required)
- `lib_roots`: import search roots
- `backend_config`: path to backend template config
- `env`: key/value env vars for interpolation

CLI `--lib` roots are searched before `.asdlrc` `lib_roots`.

## Compile command
Generate netlist from an entry file:
```bash
asdlc netlist path/to/file.asdl --backend sim.ngspice
```

Useful flags:
- `-o/--output <path>`: output file
- `--config <path>`: explicit `.asdlrc`
- `--lib <dir>`: extra library root (repeatable)
- `--verify` / `--no-verify`: toggle verification passes

## Common pitfalls
- Forgetting `top` when multiple modules exist.
- Using non-list values under `nets`.
- Using pattern delimiters in literal identifiers.
- Defining a device backend without `template`.
- Expecting AST parse to do semantic checks (many checks happen later in verification/lowering).

## Practical checklist before commit
- File parses as valid YAML.
- `instances` are inline strings.
- Every endpoint in `nets` is a string token.
- Exported ports use `$` prefix intentionally.
- Device backend templates exist for your selected backend.
- `asdlc netlist ...` runs cleanly with no error diagnostics.
