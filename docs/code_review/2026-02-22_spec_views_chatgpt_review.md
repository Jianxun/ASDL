([Past chat][1])([Past chat][2])([Past chat][2])([Past chat][2])

Nice — this is a clean, “design as code” way to get multi-view without file-name heuristics. The two specs are already close to something implementable. The places I’d tighten are mostly about **(a) naming collisions**, **(b) path/match semantics**, and **(c) a couple of consistency nits**.

## 1) Decorated module symbol (`cell@view`) spec: key edge cases

### A. Reserve `default` as a keyword (otherwise it’s ambiguous)

Right now, `view_order` uses a magic token `default`, but your `view` grammar would also allow a literal view named `default` (i.e. `cell@default`). That creates ambiguity.

**Suggestion (v0):**

* Disallow `view == "default"` in decorated symbols.
* Treat undecorated `cell` as the only “default view”.

Add to validation requirements:

* Reject `cell@default` with a targeted diagnostic (“`default` is reserved; use undecorated `cell`”).

### B. Emission name mapping: `cell_<view>` can collide

`cell_<view>` is readable, but it can collide with a real cell named that already:

* Existing cell: `ota_nmos_behav`
* Decorated realization: `ota_nmos@behav` → emits `ota_nmos_behav` (collision)

**A collision-proof deterministic mapping (still SPICE-safe):**

* Define an escaping function for tokens and use a separator that cannot appear unescaped.

One practical scheme:

* `esc(s) = s.replace("_", "__")`
* Default emits: `emit(cell) = cell`
* Decorated emits: `emit(cell@view) = esc(cell) + "_" + esc(view)`

Examples:

* `ota_nmos@behav` → `ota__nmos_behav`
* `ota__nmos@behav` → `ota____nmos_behav` (still unique)

This is deterministic and avoids the common suffix collision class.

If you don’t care about reversibility and want extra safety, another approach is `cell__V__<view>` plus *explicit collision detection* (fail if emitted name already exists). But the escaping approach is nicer because it *prevents* collisions structurally.

### C. Sanitization policy should be fully specified

You mention “deterministic, sanitized” but don’t define sanitization. Since `cell` and `view` are already constrained to `[A-Za-z0-9_]+`, you can make sanitization essentially “identity + escaping” (like above), rather than best-effort replacement.

**Recommendation:** define sanitization as a normative algorithm (not prose) so everyone emits identical netlists.

### D. Clarify “availability” when selecting from `view_order`

In the binding spec, baseline picks “first available candidate”. Explicitly define:

* A candidate `cell` / `cell@v` is “available” iff a module definition with that exact `module_symbol` exists in the loaded design symbol table.

This matters if you later support libraries/namespaces; you’ll want the lookup to be unambiguous.

---

## 2) View binding config spec: consistency + semantics that will bite

### A. Fix naming inconsistencies in the examples

You use both `behav` and `behave`:

* Module symbol examples: `@behav`
* Config example: `view_order: [default, behave]` and binds to `@behave`

Pick one token (`behav` is common) and use it consistently across both specs.

Also: `view_order: [default, behave]` means “prefer default first”, which defeats the point of preferring a behavioral view. Typically you want:

* `view_order: [behav, default]` (prefer behav, fallback to default)

### B. Path semantics are currently self-contradictory

You define:

* Path is dot-separated hierarchy; leaf segment is instance name
  …but then also say in sidecar:
* `path` excludes `instance`
  …and the earlier example path (`tb.dut.Tgate<25>`) looks like it includes an instance.

You can fix this cleanly by making **one canonical rule**:

**Canonical model (recommended):**

* `instance_path = <top>.(...parents...).<instance>`
* In config:

  * `match.path` refers to the **parent** instance path (no leaf)
  * `match.instance` refers to the leaf instance name
* In sidecar:

  * keep `{path, instance}` exactly as you already wrote
  * optionally also include `inst_path` (full path) for convenience/uniqueness

Then define scope behavior explicitly:

* If `match.instance` is present: match **only direct children** of `match.path` (or root if omitted).
* If `match.module` is present: match **all instances in the subtree** rooted at `match.path` (or whole design if omitted).

This keeps `instance` matching precise and predictable, while still allowing subtree/module sweeps.

### C. What does `module` predicate match against when the instance is decorated?

You already require `match.module` be undecorated. Good. But define semantics:

* For an instance referencing `cell@view`, its logical cell identity is still `cell`.
* `match.module` compares against the logical `cell` portion of the referenced symbol (before or after resolution — choose one and specify).

I’d recommend: **match against the logical cell identity of the instance’s *authored* reference**, so rules are stable regardless of baseline view selection.

### D. Rules overriding explicitly-decorated authored refs

Your algorithm says baseline doesn’t change authored decorated refs, but later you apply rules which “set resolved symbol”. That implies rules *can* override even explicitly-decorated instances.

That’s probably what you want (power tool), but call it out:

* “Rules apply to all instances, including those with explicitly decorated authored refs.”

If you *don’t* want that in v0, you need a “locked if authored decorated” policy (but you said advanced toggles are out of scope, so I’d keep it simple: **rules override everything**).

### E. Deterministic traversal order should be nailed down

“Deterministic traversal order” is necessary but vague. Pick one:

**Recommended:**

* Pre-order depth-first traversal
* Children visited in the exact order they appear in the module’s `instances` list (author order)

That stays stable under renaming and avoids surprising “sorted by name” behavior.

### F. Sidecar: include `inst_path` (optional but very useful)

Your `{path, instance}` pair is fine, but downstream tools often want a single key. Adding:

* `inst_path: "<path>.<instance>"` (or just instance when `path == ""`)

…makes it easy to index, diff, and debug.

---

## 3) Validation & diagnostics: a few upgrades worth adding in v0

### A. Decorated symbol parsing errors should be crisp

You already require diagnostics to identify `cell` vs `view` vs `@` cardinality. Add a few concrete cases:

* `foo@@bar` → “multiple `@` separators”
* `foo@bar@baz` → “too many `@` separators”
* `@bar` → “missing cell token”
* `foo@` → “missing view token”
* `foo@default` → “reserved view token `default`”

### B. Emission-name collision should be a hard error

Even with escaping, you should still do a final “no duplicates” check on emitted simulator-facing names, and error if any collide (e.g., someone defined a literal module named `ota__nmos_behav` that collides with your mapping).

---

## 4) Two small “design pressure” points to decide now (v0-safe)

1. **Do you want view tokens to be global or per-cell?**
   Your model implies tokens are global (“behav”, “cascode”, “lite”). That’s good. But make it explicit: tokens have no intrinsic meaning; they’re just selectors.

2. **Do you expect multiple source files/libraries to define the same `cell@view`?**
   If yes, you’ll need a precedence/merge story (out of scope, but your loader should at least detect duplicates and fail loudly in v0).

---

## Minimal edits I’d make to the specs right away

* Reserve `default` (disallow `@default`).
* Fix `behav`/`behave` inconsistencies and flip the `view_order` example to `[behav, default]`.
* Specify a collision-proof emission mapping (escaping underscores) rather than `cell_<view>` as-is.
* Clarify `match.path` meaning + direct-child vs subtree semantics depending on `instance` vs `module`.
* Specify traversal order (preorder DFS + author order).

If you want, I can rewrite both specs into a tighter “normative” form (same content, fewer ambiguities) while keeping v0 scope unchanged.

[1]: https://chatgpt.com/c/6958b585-f43c-8333-ba1d-61296df3c149 "xDSL Compiler Feature Plan"
[2]: https://chatgpt.com/c/69523038-7800-8325-8ddc-6db4df1abd40 "ASDL Design Overview"
