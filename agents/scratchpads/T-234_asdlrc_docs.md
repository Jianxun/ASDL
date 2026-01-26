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
- 2026-01-26 00:05 — Committed scratchpad updates as 7c511d9; next step open PR and set status to ready_for_review.
- 2026-01-26 00:06 — Opened PR https://github.com/Jianxun/ASDL/pull/247; next step set task to ready_for_review.
- 2026-01-26 00:07 — Set T-234 status to ready_for_review with PR 247; next step push final commit.
- 2026-01-26 04:05 — Review intake; confirmed PR context and scope; set status to review_in_progress; next step verify logs and docs accuracy.
- 2026-01-26 04:06 — Verified required check/logs present (py_compile) in scratchpad; next step scope and accuracy review of docs.
- 2026-01-26 04:07 — Reviewed README/spec updates against CLI config behavior; scope matches DoD and docs align with implementation; next step issue review decision.
- 2026-01-26 04:08 — Posted PR review comment ([Reviewer]: review clean) and set status to review_clean; next step close out and merge.

## Patch summary
- Documented .asdlrc schema, discovery, interpolation, and precedence in `README.md`.
- Updated `docs/specs/spec_cli.md` with --config, .asdlrc rules, and import root ordering.

## PR URL
- https://github.com/Jianxun/ASDL/pull/247

## Status request (Done / Blocked / In Progress)
- Ready for review.

## Next steps
- Reviewer to validate docs and merge PR when approved.
