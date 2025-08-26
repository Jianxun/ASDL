## Parser Test Refactor TODO

### Phase 0 — Direction
- [X] Decide imports direction: simple file path strings; consolidate to P-codes
- [X] Introduce parser XCCSS diagnostics module and migration plan

### Phase 1 — Consolidation and Cleanup
- [ ] Consolidate YAML/root tests into single P100/P101 suite
- [ ] Parameterize P200 unknown top-level test; remove duplicates
- [ ] Centralize location tests; remove redundant assertions elsewhere

### Phase 2 — Add Missing Tests (Existing Behavior)
- [ ] Add P104 test: port missing dir in PortParser
- [ ] Add P104 test: instance missing model in InstanceParser
- [ ] Add P105 test: port parsing error (bad enum)
- [ ] Assert P301/P302 codes in dual-syntax warning tests
- [X] Replace ImportParser diagnostics to P0501/P0502; update tests
- [X] Align imports tests to simple path + P0501/P0502 (no P106)

### Phase 3 — Implement Duplicate Detection + Tests
- [ ] Implement P0232 duplicate module name detection + tests
- [ ] Implement P0242 duplicate port name detection + tests
- [ ] Implement P0251 duplicate instance name detection + tests
- [ ] Implement P0221 duplicate import alias detection + tests

### Phase 4 — Enum Validation + Tests
- [ ] Implement P0501 invalid port direction enum + tests
- [ ] Implement P0502 invalid port type enum + tests

### Phase 5 — Docs Alignment and Optional Diagnostics
- [ ] Add optional INFO diagnostic for empty file (P0103)
- [ ] Update error-code docs per P104 vs P0240/P0250 decision

### Phase 6 — Test Environment Hygiene
- [ ] Remove test sys.path hacks; rely on pyproject pythonpath

