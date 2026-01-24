# T-218 — Clarify NetlistIR no-leading-$ literal-name policy

## Task summary (DoD + verify)
- DoD: Confirm NetlistIR literal names never include a leading `$` (nets, module ports, instance names, instance ref symbols, and instance conn port names). Align verifier behavior (no-leading-$ across all fields), diagnostic text, and tests. Update diagnostic/spec text to state that `$` is syntax sugar stripped before NetlistIR, and add unit tests that cover leading `$` violations for each NetlistIR name field.
- Verify: `venv/bin/pytest tests/unit_tests/emit/test_netlist_ir_verify.py -v`

## Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

## Plan
- Review current NetlistIR verification and diagnostics for leading `$` handling.
- Update verifier/diagnostic messaging to enforce no-leading-$ across all NetlistIR name fields.
- Extend unit tests to cover each field, plus docs/spec updates.
- Run verify command and record results.

## Progress log
- 2026-01-24 01:02 — Task intake and context review; created scratchpad; set T-218 in_progress; ran lint_tasks_state.py; created branch feature/T-218-netlist-ir-literal-policy; next step: review verifier/tests/specs for leading `$` policy gaps.
- 2026-01-24 01:03 — Confirmed task scope: NetlistIR literal names must not carry leading `$`; align verifier text, specs, and tests across nets/ports/instances/refs/conn ports; next step: add tests.
- 2026-01-24 01:03 — Commit cdc0759: start task state + scratchpad.
- 2026-01-24 01:03 — Commit 0a2a0b6: add leading `$` literal-name tests for NetlistIR fields; next step: align verifier messaging and spec text.
- 2026-01-24 01:04 — Updated NetlistIR verifier messages and spec/diagnostic text for no-leading-`$` policy; next step: commit changes and run verification.

## Patch summary
- TBD

## PR URL
- TBD

## Verification
- TBD

## Status request
- In Progress

## Blockers / Questions
- None.

## Next steps
- Review NetlistIR verifier/tests/specs and implement leading `$` coverage.
