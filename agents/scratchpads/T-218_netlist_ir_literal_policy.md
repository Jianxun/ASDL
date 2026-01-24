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
- 2026-01-24 01:04 — Commit f436cb4: align verifier literal-name messaging and update NetlistIR/spec diagnostic text.
- 2026-01-24 01:05 — Ran `venv/bin/pytest tests/unit_tests/emit/test_netlist_ir_verify.py -v`; all tests passed.
- 2026-01-24 01:06 — Pushed branch and opened PR https://github.com/Jianxun/ASDL/pull/222.
- 2026-01-24 01:06 — Set T-218 status to ready_for_review with PR #222; ran lint_tasks_state.py.
- 2026-01-24 01:06 — Commit 8305b2d: update task status + scratchpad with PR/verification details.
- 2026-01-24 01:10 — Review intake: set T-218 status to review_in_progress; next step confirm PR base, scope, and verification logs.
- 2026-01-24 01:11 — Confirmed PR #222 targets main; scratchpad and verification logs present; next step review scope and code changes.
- 2026-01-24 01:12 — Verified required pytest command via scratchpad log (not rerun); next step complete scope review against DoD.
- 2026-01-24 01:13 — Scope review complete: changes align with T-218 DoD, including verifier messaging, specs, and tests; next step finalize review decision.
- 2026-01-24 01:14 — Review decision: clean; posted PR comment with verification note; set status to review_clean; next step merge and closeout.
- 2026-01-24 01:16 — Merge prep: set T-218 status to done (merged true) for closeout; next step run lint, push, then merge PR and clean branches.

## Patch summary
- Added parameterized verifier tests covering leading `$` in each NetlistIR name field.
- Updated NetlistIR verifier messaging to call out no-leading-`$` literal names.
- Clarified NetlistIR/spec diagnostic text to note `$` is stripped before NetlistIR.

## PR URL
- https://github.com/Jianxun/ASDL/pull/222

## Verification
- `venv/bin/pytest tests/unit_tests/emit/test_netlist_ir_verify.py -v`

## Status request
- Ready for Review

## Blockers / Questions
- None.

## Next steps
- Open PR, update task status to ready_for_review, and record the PR URL.
