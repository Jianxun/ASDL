# Spec - CLI Query Subsystem (`asdlc query`) v0

## Purpose
Define a single query-oriented CLI surface for inspecting ASDL designs across
authoring, view-resolution, and emission planning stages.

---

## Scope (v0)
- One command group: `asdlc query`.
- Subcommands:
  - `tree`
  - `bindings`
  - `emit-plan`
  - `refs`
  - `instance`
  - `net`
  - `net-trace`
- Deterministic, machine-readable JSON output plus human-readable text output.
- Stage-aware queries via `--stage authored|resolved|emitted`.

Out of scope (v0):
- Arbitrary query DSL.
- Mutation/edit operations.
- Performance indexing/caching guarantees.

---

## Command Surface
```
asdlc query <subcommand> <entry.asdl> [options]
```

Common options:
- `--config <path>`: explicit `.asdlrc` path (same behavior as `asdlc netlist`).
- `--lib <dir>`: repeatable import root override (same precedence semantics).
- `--view-config <path>`: view binding config YAML path.
- `--view-profile <name>`: selected profile in `--view-config`.
- `--top <module>`: override selected top module where supported.
- `--stage authored|resolved|emitted`:
  - default: `resolved`
- `--json`: emit JSON payload only.

Rules:
- `--view-profile` requires `--view-config`.
- `--stage emitted` uses final resolved top realization semantics and
  reachable-only emission planning.
  - when `--view-config/--view-profile` are omitted, emitted-stage queries use
    baseline view resolution only (no rule overrides).

---

## Stage Semantics

### `authored`
- Reflects raw authored design references from parsed ASDL (before view binding).
- Uses authored module symbols exactly as declared.

### `resolved`
- Reflects post view-binding module references after `view_order` baseline and
  ordered rule application.
- Includes rule attribution where applicable (for example `rule_id`).

### `emitted`
- Reflects netlist-facing realization and naming:
  - final resolved top realization
  - reachable-only module set
  - emitted names (`cell`, `cell_<view>`, collision suffixes)

---

## Subcommands

### `asdlc query tree`
Purpose:
- Show hierarchical instance tree rooted at top.
- Includes both module instances and device instances (devices are leaves).
- Hierarchy traversal semantics are defined by
  `docs/specs/spec_hierarchy_traversal.md` with `include_devices=True`.

Options:
- supports common options.
- `--compact-view/--verbose-view`: choose compact (default) or verbose payload.
  - default is `--compact-view`.

Verbose JSON payload fields (`--verbose-view`):
- `path: str`
- `parent_path: str | null`
- `instance: str | null` (null at root)
- `authored_ref: str`
- `resolved_ref: str | null`
- `emitted_name: str | null`
- `depth: int`
- `children: dict[str, TreeNode]` (keyed by child instance name)

`TreeNode` is recursive and uses the same fields listed above.

Compact JSON payload shape (default, `--compact-view`):
- recursive dictionary
- key format: `<instance>:<resolved_ref>`
- value: nested child mapping (empty object for leaves)
- JSON output is pretty-printed for readability in compact mode.

Default non-JSON output (`--compact-view`):
- ASCII hierarchy tree using the same `<instance>:<resolved_ref>` labels.

### `asdlc query bindings`
Purpose:
- Show resolved view bindings per instance occurrence.

Options:
- requires `--view-config` and `--view-profile`.
- supports `--json`.

JSON entry fields:
- `path: str`
- `instance: str`
- `authored_ref: str`
- `resolved: str`
- `rule_id: str | null`

### `asdlc query emit-plan`
Purpose:
- Show emission planning summary and module-level mapping in emitted stage.

Options:
- supports common options.

JSON payload fields:
- `top_authored: str`
- `top_resolved: str`
- `top_emitted: str`
- `reachable_modules: list[EmitModule]`
- `pruned_modules: list[PrunedModule]`

`EmitModule` fields:
- `symbol: str`
- `file_id: str`
- `base_name: str`
- `emitted_name: str`
- `renamed: bool`

`PrunedModule` fields:
- `symbol: str`
- `file_id: str`
- `reason: str` (v0 value: `unreachable_from_final_top`)

### `asdlc query refs`
Purpose:
- Find instance occurrences referencing a target module symbol/cell.

Options:
- `--module <symbol>` (required): exact symbol match in v0 (accepts either
  undecorated or decorated input, but does not wildcard-match variants).
- supports common options.

JSON entry fields:
- `path: str`
- `instance: str`
- `authored_ref: str`
- `resolved_ref: str | null`
- `emitted_name: str | null`

### `asdlc query instance`
Purpose:
- Inspect one instance occurrence by canonical path.

Options:
- `--path <inst_path>` (required)
- supports common options.

JSON payload fields:
- `path: str`
- `parent_path: str | null`
- `instance: str`
- `authored_ref: str`
- `resolved_ref: str | null`
- `rule_id: str | null`
- `emitted_name: str | null`
- `children: list[str]`
- `connected_nets: list[str]`

### `asdlc query net`
Purpose:
- Inspect one net and all connected instance terminals in scope.

Options:
- `--module <module_symbol>` (required for disambiguation)
- `--net <net_name>` (required)
- supports common options.

JSON payload fields:
- `module: str`
- `net: str`
- `stage: str`
- `connections: list[Connection]`

`Connection` fields:
- `instance_path: str`
- `instance: str`
- `terminal: str`
- `resolved_ref: str | null`

### `asdlc query net-trace`
Purpose:
- Trace equivalent net references across hierarchy for a selected net anchor.

Options:
- `--module <module_symbol>` (required for disambiguation)
- `--net <net_name>` (required)
- `--path <instance_path>` (optional anchor scope)
- `--direction up|down|both` (default: `both`)
- `--order dfs-pre|dfs-post` (default: `dfs-pre`; ordering only)
- supports common options.

Semantics:
- Query meaning is net-equivalence tracing, not generic graph traversal.
- Traversal order controls deterministic row ordering of trace results.

JSON payload fields:
- `anchor: TraceAnchor`
- `stage: str`
- `equivalents: list[TraceEquivalent]`
- `connections: list[Connection]`

`TraceAnchor` fields:
- `module: str`
- `net: str`
- `path: str | null`

`TraceEquivalent` fields:
- `path: str`
- `module: str`
- `net: str`
- `relation: str` (`self`, `up`, `down`)
- `resolved_ref: str | null`

---

## Diagnostics and Exit Codes
- Diagnostics follow the shared diagnostic contract.
- Exit codes:
  - `0`: success.
  - `1`: query resolution error, invalid arguments, or any error diagnostic.
- Query failures must emit diagnostics rather than uncaught exceptions.

---

## Determinism
- For fixed inputs/options, output row ordering must be deterministic.
- JSON object keys should be stable in tests (`sort_keys=True` in serializer
  paths where available).

### Deterministic ordering keys (v0)
- `tree`: recursive `children` map order is deterministic and keyed by child
  instance name.
- `bindings`: `(path, instance)`.
- `emit-plan.reachable_modules`: deterministic emission traversal order.
- `emit-plan.pruned_modules`: `(symbol, file_id)`.
- `refs`: `(path, instance, authored_ref, resolved_ref_or_empty)`.
- `instance.children`: authored declaration order.
- `instance.connected_nets`: deterministic lexical order in v0 (provisional;
  may evolve to declaration/structural order after usage validation).
- `net.connections`: `(instance_path, terminal)`.
- `net-trace.equivalents`: traversal order per `--order`, tie-break by
  `(path, module, net)`.
- `net-trace.connections`: `(instance_path, terminal)`.

### JSON envelope (v0)
Every JSON payload includes:
- `schema_version: int` (v0 uses `1`)
- `kind: str` (payload discriminator)

`kind` values:
- `query.tree`
- `query.tree.compact`
- `query.bindings`
- `query.emit_plan`
- `query.refs`
- `query.instance`
- `query.net`
- `query.net_trace`

### Empty-result and anchor semantics (v0)
- Missing/invalid anchors (`instance`, `net`, `module`) are hard errors with
  diagnostics and exit code `1`.
- Valid queries with zero matches return a successful empty payload (exit `0`).

---

## Traversal Order Semantics
Traversal-related query outputs (for example hierarchical listings and future
explicit traversal modes) use these terms:

- `dfs-pre` (depth-first preorder):
  - visit parent before children
  - order shape: `parent -> child -> grandchild`
  - preferred for top-down inspection and execution planning

- `dfs-post` (depth-first postorder):
  - visit children before parent
  - order shape: `grandchild -> child -> parent`
  - preferred for bottom-up aggregation/roll-up operations

Example hierarchy:
- `tb`
- `tb.dut`
- `tb.dut.stage1`
- `tb.dut.stage2`

Then:
- `dfs-pre`: `tb, tb.dut, tb.dut.stage1, tb.dut.stage2`
- `dfs-post`: `tb.dut.stage1, tb.dut.stage2, tb.dut, tb`

---

## Relationship to Other Specs
- Netlist CLI behavior: `docs/specs/spec_cli.md`
- View binding resolution: `docs/specs/spec_asdl_view_config.md`
- View-decorated symbol/emission semantics: `docs/specs/spec_asdl_views.md`

---

## Open Decisions (v0.x)
The following items remain intentionally deferred while implementation and
semantic experiments proceed.

1. Path canonicalization:
- Final canonical path encoding for instance names that include pattern/range
  expansion syntax (for example `Tgate<2>`), including escaping rules.

2. `net-trace` equivalence boundaries:
- Whether equivalence crossing is only through hierarchical port boundaries or
  may include additional aliasing rules.
- How emitted-name remapping should be represented in trace output.

3. Direction and stopping semantics:
- Precise stopping rules for `--direction up|down|both` (root/leaf/max-depth
  interactions).

4. Query diagnostics taxonomy:
- Whether to reserve query-specific diagnostic codes (`QRY-xxx`) or continue
  formal reuse of existing CLI/tool diagnostics.

5. `instance.connected_nets` ordering:
- Whether to keep lexical ordering or switch to declaration/structural ordering
  after user-facing behavior validation.
