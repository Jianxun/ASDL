# ASDL Schema Generator – Todo Tracker

Reference: `ASDL/src/asdl/data_structures.py` is the single source of truth. Work will focus on introspecting dataclasses and enums to generate both JSON Schema and a human-readable schema (no static text).

Legend: [ ] pending, [x] done

## Current Sprint (Phase A – Core Generator)
- [ ] Decide exclusion strategy for runtime-only fields in `Locatable`
  - [ ] Option A: class-level `__schema_exclude_fields__` on `Locatable`
  - [ ] Option B: per-field `field(metadata={"schema": {"include": False}})`
  - [ ] Implement chosen approach and document in code
- [ ] Implement dataclass introspection → JSON Schema generator
  - [ ] Handle: Enums, Optional[T], List[T], Dict[str, T], Any
  - [ ] Treat dicts as `additionalProperties: schema(T)` and support key hints
  - [ ] Mark required vs optional based on annotations/defaults
- [ ] Implement human-readable text renderer from the JSON Schema (no static text)
  - [ ] Show root structure, field groups, required flags, enum choices
  - [ ] Improve readability for dict-typed maps (e.g., `models`, `modules`)
- [ ] Wire CLI `asdlc schema` to new generator
  - [ ] `asdlc schema` → text to stdout
  - [ ] `asdlc schema --json` → JSON Schema to stdout
  - [ ] `--out DIR` writes `schema.json` and `schema.txt`
- [ ] Replace script: make `ASDL/scripts/generate_schema.py` call new generator
- [ ] Remove duplication: deprecate and then delete `src/asdl/schema_models.py`

## Phase B – Metadata & Docs
- [ ] Add minimal `field(metadata={"schema": {"description": "..."}})` where helpful
  - [ ] `DeviceModel.type`, `Module.ports`, `Instance.mappings`, etc.
- [ ] Support optional `key_name` metadata for dict fields to improve text rendering
- [ ] Add display ordering (optional) for nicer text output
- [ ] Documentation
  - [ ] Document the generator in developer docs and CLI docs
  - [ ] Note exclusion of `Locatable` fields and rationale
  - [ ] Add a section on how to annotate fields for schema docs

## Phase C – Packaging & CI
- [ ] Ensure `schema.txt` and `schema.json` can be generated reproducibly in CI (no drift)
- [ ] Optionally include `schema.txt` in sdist/wheel (confirm decision)
- [ ] Add tests to prevent accidental re-introduction of `Locatable` fields

## Tests
- [ ] Unit: mapping rules (Enum values, Optional detection, arrays, dicts)
- [ ] Snapshot: top-level JSON Schema structure (selected subsets)
- [ ] Text renderer: smoke test for key sections and required markers
- [ ] Guard: `Locatable` fields excluded from schema

## Acceptance Criteria
- [ ] `asdlc schema` and `--json` reflect `data_structures.py` faithfully
- [ ] No static strings for schema content; text output is rendered from JSON Schema
- [ ] Tests cover core mapping rules and exclusion of runtime-only fields
- [ ] No duplication of schema definitions in the codebase

## Notes / Decisions
- [ ] Confirm exclusion strategy for `Locatable`
- [ ] Confirm whether to ship `schema.txt` in distribution artifacts

## Completed
- [x] Create schema generator tracking file `context/todo_schema.md`
