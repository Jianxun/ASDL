# ASDL Import Mechanism Spec (v0.1)

This spec defines how ASDL YAML files declare imports, how the compiler resolves them, and how imported symbols are referenced.

---

## 1. Goals

- Enable multi-file “codebase-style” circuit authoring.
- Deterministic, reproducible builds.
- Explicit namespaces to avoid accidental name collisions.
- Transitive loading of dependencies without “spooky” name leakage.

Non-goals (v0.1):
- Package versioning / semver
- Remote fetching
- Cyclic imports
- Implicit wildcard import into global scope

---

## 2. Syntax

### 2.1 `imports` section

`imports` is a top-level mapping of **namespace** to **path** using the `<ns>:<path>` style:

```yaml
imports:
  gf: gf180/primitives.asdl
  al: analogLib.asdl
  lib: ./lib/shift_register.asdl
```

- Keys are namespaces (`ns`).
- Values are import paths (`path`).

### 2.2 Namespaces

- `ns` MUST match: `[A-Za-z_][A-Za-z0-9_]*`
- Namespaces are local to the importing file (lexical).
- Namespace collisions within a file are errors.

### 2.3 Referencing imported symbols

Imported symbols MUST be referenced as:

- `ns.symbol_name`

Examples:
- `gf.nfet_03v3`
- `al.vdc`
- `lib.shift_register`

Unqualified symbol references MAY be used only for symbols defined in the
same file; they never search imported namespaces.

---

## 3. Path Resolution

### 3.1 Path forms

An import path resolves to a **single file** (e.g., `./lib/shift_register.asdl`).
Directories are not valid import targets in v0.1.
The compiler does not add file extensions; the path must resolve to an existing
file as written.

### 3.2 Resolution algorithm

Given an importing file `F` and an import path `P`:

1. If `P` starts with `./` or `../`:
   - resolve relative to directory of `F`.

2. Else if `P` is an absolute filesystem path:
   - use as-is.

3. Else (logical path):
   - search in ordered roots:
     1) project root (`--root`, default: entry file directory)
     2) include roots (`-I <dir>`, in CLI order)
     3) library roots (`--lib <name>=<dir>`, in CLI order; optional; name does not affect resolution)

After a candidate path is found, the compiler MUST normalize it by collapsing
`.`/`..` segments and converting to an absolute path (no symlink resolution).

First match wins. If multiple matches exist, the compiler MAY warn.

If no match is found, it is an error.

---

## 4. Loading vs Visibility

### 4.1 Transitive loading

Imports are transitive for **loading**:
- If `A` imports `B`, and `B` imports `C`, the linker loads `C` as part of the program.

### 4.2 Non-transitive visibility

Imports are NOT transitive for **visibility**:
- `A` does not automatically gain a namespace binding for `C` via `B`.
- `A` may only reference symbols through namespaces declared in `A.imports`.

This prevents implicit name leakage.

---

## 5. Symbol Tables

### 5.1 ProgramDB (global registry)

The compiler constructs a global registry of all loaded definitions:

- `ModuleKey = (file_id, module_name)`
- `DeviceKey = (file_id, device_name)`
- (future: views, templates, etc.)

`file_id` is the resolved canonical path of the imported file (absolute path,
with `.`/`..` segments collapsed; no symlink resolution).

Each symbol stores:
- kind (`module`, `device`, ...)
- definition (AST handle)
- source location (file + span) for diagnostics

### 5.2 Per-file Name Environment (lexical bindings)

For each file `F`, build:
- `NameEnv_F : ns -> file_id`

Resolution of `ns.symbol`:
1) lookup `ns` in `NameEnv_F`
2) lookup `symbol` in `ProgramDB` under that `file_id`

If either fails: error.

Resolution of an unqualified `symbol`:
- lookup `symbol` in the current file’s definitions only
- if missing: error

---

## 6. Conflicts and Errors

### 6.1 Duplicate symbol definitions within a file

If a file defines two symbols with the same spelling (regardless of kind):
- ERROR (v0.1)

### 6.2 Namespace binding conflicts

If a file defines:
```yaml
imports:
  gf: gf180/primitives.asdl
  gf: sky130/primitives.asdl
```
- ERROR (duplicate mapping key; YAML itself typically prevents this)

If a file defines a local symbol that shares the same *spelling* as a namespace (e.g., module named `gf`):
- Allowed, since references are qualified and namespaces only appear before `.`.
- Linter MAY warn to avoid confusion.

If multiple namespaces resolve to the same file:
- Allowed (distinct namespace bindings to the same `file_id`).

### 6.3 Cyclic imports

If the import graph contains a cycle:
- ERROR (v0.1)
- The error MUST report an import chain showing the cycle.

### 6.4 Unused imports

If a declared namespace is never referenced:
- Compiler SHOULD emit a warning.

---

## 7. Re-exports (Optional Extension)

Re-exports allow a file to act as a façade by exposing selected symbols from its own imports.

Not required in v0.1. If implemented, use:

```yaml
reexports:
  gf: [nfet_03v3, pfet_03v3]
  al: ["*"]
```

Rules:
- Re-exported names become part of the file’s exported symbol set.
- Collisions between local definitions and re-exported symbols are errors unless renamed (rename support may be added later).

Visibility remains lexical:
- Importing the façade file provides access only via its namespace (e.g., `std.nmos`), not by importing underlying files.

---

## 8. Examples

### 8.1 Typical project top

```yaml
imports:
  gf: gf180/primitives.asdl
  al: analogLib.asdl
  std: ./libs/std_gf180.asdl

modules:
  top:
    instances:
      MN1: std.nmos L=0.5u W=5u
    nets:
      $IN:
        - MN1.G
      $OUT:
        - MN1.D
      VSS:
        - MN1.S
        - MN1.B
```

### 8.2 Two design files with transitive loading (no transitive visibility)

`A.asdl`:
```yaml
imports:
  lib: ./B.asdl
modules:
  top:
    instances:
      U1: lib.block
    nets:
      $IN:
        - U1.IN
      $OUT:
        - U1.OUT
      VSS:
        - U1.VSS
```

`B.asdl`:
```yaml
imports:
  gf: gf180/primitives.asdl
modules:
  block:
    instances:
      MN1: gf.nfet_03v3 L=0.5u W=5u
    nets:
      $IN:
        - MN1.G
      $OUT:
        - MN1.D
      VSS:
        - MN1.S
        - MN1.B
```

`A.asdl` cannot reference `gf.*` unless it imports `gf` itself.

---

## 9. Determinism Requirements

A build is deterministic if:
- import resolution order is stable
- symbol registration order does not affect resolution
- resolution always uses the “first match wins” ordered root list

The compiler MUST produce byte-identical outputs given identical input files and identical root lists.

---
