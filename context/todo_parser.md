## Parser Test Refactor TODO

### Phase 0 — Direction
- [X] Decide imports direction: simple file path strings; consolidate to P-codes
- [X] Introduce parser XCCSS diagnostics module and migration plan

### Phase 1 — Consolidation and Cleanup
- [X] Consolidate YAML/root tests into single P100/P101 suite
- [X] Parameterize P200 unknown top-level test; remove duplicates
- [X] Centralize location tests; remove redundant assertions elsewhere
  - [X] Remove `test_unified_parsing.py` and rely on per-code tests for negatives
  - [X] Keep positive-path coverage in `test_parser_positive_paths.py`

### Phase 2 — Add Missing Tests (Existing Behavior)
- [X] Add P0240 test: port missing dir in PortParser
- [X] Add P0250 test: instance missing model in InstanceParser
- [X] Add P0205 test: port parsing error (bad enum)
- [X] Assert P0601/P0602 codes in dual-syntax warning tests
- [X] Replace ImportParser diagnostics to P0501/P0502; update tests
- [X] Align imports tests to simple path + P0501/P0502 (no P106)

### Phase 3 — Duplicate Handling Strategy
- [X] Parser: Treat duplicate YAML keys as P0101 (ruamel DuplicateKeyError)
- [X] Parser: Forbid YAML merge keys (<<) → P0101
- [ ] Elaborator: Detect duplicate module names across imports (moved here)
- [ ] Elaborator: Detect duplicate port/instance names after pattern expansion
- [ ] Elaborator: Detect duplicate import alias after resolution/normalization

### Phase 4 — Enum Validation + Tests
- [X] Implement P0511 invalid port direction enum + tests
- [X] Implement P0512 invalid port type enum + tests

### Phase 5 — Docs Alignment and Optional Diagnostics
- [X] Add optional INFO diagnostic for empty file (P0103)
- [X] Update error-code docs per P104→P0240/P0250 and P301/302→P0601/0602 migration

### Phase 6 — Test Environment Hygiene
- [ ] Remove test sys.path hacks; rely on pyproject pythonpath

