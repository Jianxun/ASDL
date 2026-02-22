# Spec - ASDL View Binding Config v0

## Purpose
Define profile-based binding resolution for view-decorated module symbols and
the inspectable sidecar output consumed by lowering/emission workflows.

---

## Scope (v0)
- Profile schema (`view_order`, ordered `rules`).
- Match semantics (`path`, `instance`, `module`).
- Deterministic resolution algorithm.
- Sidecar schema for resolved instance bindings.

Out of scope:
- CLI flag design and UX.
- Rule wildcards/regex syntax beyond existing instance/path naming rules.
- Advanced policy toggles (for example force-override authored decorated refs).

---

## Top-level schema

Config file is a mapping of profile name to profile object:

```yaml
config_3:
  description: Testbench for swmatrix row
  view_order: [default, behave]
  rules:
    - id: sr_behav
      match: {path: tb.dut, instance: SR_row}
      bind: ShiftReg_row_25@behave
    - match: {module: swmatrix_Tgate}
      bind: swmatrix_Tgate@behave
```

### Profile fields
- `description: str` (optional)
- `view_order: list[str]` (required, non-empty)
- `rules: list[Rule]` (optional, default empty)

`view_order` tokens:
- `default`: undecorated symbol (`cell`)
- `<view>`: decorated symbol candidate (`cell@<view>`)

---

## Rule schema

### Rule fields
- `id: str` (optional)
- `match: Match` (required)
- `bind: str` (required; module symbol `cell` or `cell@view`)

If `id` is omitted, compiler assigns `rule<k>` where `k` is 1-based rule
position in the profile.

### Match fields
- `path: str` (optional)
- `instance: str` (optional; instance leaf name)
- `module: str` (optional; logical cell name, undecorated)

At least one of `path`, `instance`, `module` must be present.
`instance` and `module` are mutually exclusive in v0.

---

## Match semantics

### Instance path model
- Path format is dot-separated hierarchy rooted at selected top module
  (for example `tb.dut.Tgate<25>`).
- Leaf segment is instance name.

### Scope semantics
- If `match.path` is omitted: scope is root-level instances (instances whose
  parent is the top module).
- If `match.path` is present: scope is the subtree rooted at that path.

### Predicate semantics
Within scope, a rule matches an instance when all provided predicates hold:
- `instance`: instance leaf name equals `instance`
- `module`: instance logical referenced cell equals `module`

---

## Resolution algorithm

Given a selected profile:

1. Enumerate elaborated instance occurrences in deterministic traversal order.
2. Baseline resolution from `view_order`:
   - for undecorated ref `cell`, select first available candidate from
     `view_order`:
     - `default` -> `cell`
     - `v` -> `cell@v`
   - if no candidate exists, emit an error.
   - authored explicit decorated refs (`cell@view`) remain as authored in v0.
3. Apply rules in listed order:
   - each matching rule sets resolved symbol to `bind`
   - later matches override earlier matches
4. Final resolved symbol per instance is used by lowering/emission.

---

## Sidecar output (resolved bindings)

Compiler emits a sidecar list for inspectability:

```json
[
  {"path":"tb.dut","instance":"SR_row","resolved":"ShiftReg_row_25@behave","rule_id":"rule1"},
  {"path":"tb.dut","instance":"Tgate<25>","resolved":"swmatrix_Tgate@behave","rule_id":"rule2"}
]
```

### Sidecar fields
- `path: str` (parent hierarchy path; does not include `instance`)
- `instance: str` (leaf instance name)
- `resolved: str` (resolved module symbol `cell` or `cell@view`)
- `rule_id: str | null` (optional in payload; matched rule ID or null if only
  baseline resolution applied)

Sidecar ordering must be deterministic (stable hierarchy traversal order).

---

## Error conditions
- Empty or missing `view_order`.
- Rule missing `match` or `bind`.
- `match` object has none of `path`/`instance`/`module`.
- `match` sets both `instance` and `module` (mutually exclusive in v0).
- Invalid `bind` symbol grammar.
- `module` predicate uses decorated form.
- `match.path` does not resolve to an existing hierarchy node.
- Final `resolved` symbol not found in loaded design symbols.
