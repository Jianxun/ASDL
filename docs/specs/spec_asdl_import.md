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

In inline instance expressions, the type token may be qualified as
`ns.symbol_name` to reference imported modules/devices.

---

## 3. Path Resolution

### 3.1 Path forms

An import path resolves to a **single file** (e.g., `./lib/shift_register.asdl`).
Directories are not valid import targets in v0.1.
The compiler does not add file extensions; the path must resolve to an existing
file as written.

### 3.2 Resolution algorithm

Given an importing file `F` and an import path `P`:

0. Expand `~` and `$VAR`/`${VAR}` segments in `P` (environment variable expansion).
   If expansion fails or yields an empty path, emit `AST-011` malformed import
   diagnostics.
1. If `P` starts with `./` or `../`:
   - resolve relative to directory of `F`.

2. Else if `P` is an absolute filesystem path:
   - use as-is.

3. Else (logical path):
   - search in ordered roots:
     1) CLI `--lib` roots (repeatable, in CLI order)
     2) `ASDL_LIB_PATH` roots (PATH-style list, in order)

Search all roots in order and collect existing candidates. If exactly one
match exists, the compiler MUST normalize it by collapsing `.`/`..` segments
and converting to an absolute path (no symlink resolution). If multiple
matches exist, it is an error (no shadowing); the error MUST list all matches
in root order. If no match is found, it is an error.

`ASDL_LIB_PATH` is a PATH-style list of directories (OS path separator).
Entries expand `~` and `$VAR`/`${VAR}`; if expansion fails or yields an empty
path, emit `AST-011` and ignore that entry. Relative entries are resolved
against the current working directory; empty entries are ignored.

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

If a `file_id` is loaded multiple times (via different import paths),
the compiler MUST deduplicate it and reuse the first loaded AST.

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

### 6.5 Diagnostics codes

- `AST-010`: import path not found (ERROR)
- `AST-011`: malformed import path (ERROR)
- `AST-012`: import cycle detected (ERROR)
- `AST-013`: duplicate namespace in `imports` (ERROR)
- `AST-014`: duplicate symbol name within a file (ERROR)
- `AST-015`: ambiguous import path; multiple matches (ERROR)
- `IR-010`: unresolved qualified symbol `ns.symbol` (ERROR)
- `IR-011`: unresolved unqualified symbol (ERROR)
- `LINT-001`: unused import namespace (WARNING)

---

## 7. Pipeline integration

- Import resolution runs after parsing and before AST->NFIR conversion.
- `file_id` is the canonical absolute path (normalized `.`/`..`, no symlink resolution).
- Symbol identity is `(file_id, name)`; same-name symbols are allowed across files.
- IR propagation:
  - `ModuleOp` and `DeviceOp` carry `file_id`.
  - `InstanceOp` carries `ref_file_id` for the resolved module/device reference.
  - `DesignOp` carries `entry_file_id` for the root input file.
- Emission remains template-driven; the compiler only passes data:
  - `__subckt_header__` receives the defining module `file_id`.
  - `__subckt_call__` receives the referenced module `file_id`.
  - `__netlist_header__`/`__netlist_footer__` receive the entry `file_id`.

---

## 8. Re-exports (Optional Extension)

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

## 9. Examples

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

## 10. Determinism Requirements

A build is deterministic if:
- import resolution order is stable
- symbol registration order does not affect resolution
- resolution scans the ordered root list and errors on ambiguity (no shadowing)

The compiler MUST produce byte-identical outputs given identical input files and identical root lists.

---
