# T-234: Document .asdlrc schema + discovery rules

## Task summary (DoD + verify)
- DoD: Document the `.asdlrc` schema (schema_version, lib_roots, backend_config, env), interpolation rules, and discovery order in README and CLI spec docs. Note precedence rules and the entry-file directory search behavior.
- Verify: `./venv/bin/python -m py_compile src/asdl/cli/__init__.py`

## Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

## Plan
- 

## Progress log
- 

## Patch summary
- 

## PR URL
- 

## Verification
- 

## Status request (Done / Blocked / In Progress)
- 

## Blockers / Questions
- 

## Next steps
- 
## Plan
- Review existing README and CLI spec for config-related sections.
- Document .asdlrc schema, discovery, interpolation, and precedence.
- Run verify command and capture results.

## Progress log
- 2026-01-26 00:00 — Task intake and setup; read context files; created scratchpad; set T-234 to in_progress; next step review docs targets.
- 2026-01-26 00:01 — Updated README with .asdlrc schema, discovery, interpolation, and precedence details; next step update CLI spec.
- 2026-01-26 00:02 — Updated spec_cli with --config option and .asdlrc rules/precedence; next step commit docs changes.

## Todo
- [x] Document .asdlrc schema + discovery in README.
- [x] Document .asdlrc schema + discovery in CLI spec.
- [x] Run verify command.

## Task understanding
Document .asdlrc schema, interpolation, discovery, and precedence rules in README and CLI spec, including entry-file search behavior and --config override.
- 2026-01-26 00:03 — Committed doc updates (README/spec + task state/scratchpad) as 6f61f69; next step run verify command.
- 2026-01-26 00:04 — Verified ./venv/bin/python -m py_compile src/asdl/cli/__init__.py (ok); next step update status and prep PR.

## Verification
- ./venv/bin/python -m py_compile src/asdl/cli/__init__.py
