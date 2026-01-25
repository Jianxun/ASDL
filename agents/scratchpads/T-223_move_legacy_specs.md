# T-223 Move legacy xDSL specs under docs/legacy

## Task summary (DoD + verify)
- Relocate legacy GraphIR/IFIR/NFIR specs and xDSL-era pipeline docs from `docs/specs/` into `docs/legacy/`.
- Add a brief README in `docs/legacy/` describing decommissioned status.
- Update any in-repo references to point to the new paths.
- Verify: `venv/bin/pytest tests/unit_tests/cli -v`.

## Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

## Plan
- Inspect docs/specs for legacy xDSL-era docs and current references.
- Move identified legacy specs into docs/legacy and add README.
- Update codebase map and any doc references to new paths.
- Run verify command or document skip reason.

## Todo
- [x] Move legacy specs into `docs/legacy` and add README.
- [x] Update references (docs/codebase_map) to new paths.
- [x] Run verify command or document skip.

## Progress log
- 2026-01-25 01:20 — Moved legacy GraphIR/IFIR/NFIR + pipeline specs into `docs/legacy/` via git mv; retained tracked files despite gitignore; next step add README and fix internal refs.
- 2026-01-25 01:21 — Commit 5662cff (chore: start T-223 legacy specs move).
- 2026-01-25 01:23 — Added `docs/legacy/README.md` (forced add due to ignore) and updated internal references in moved specs; next step update repo references.
- 2026-01-25 01:23 — Commit f243bee (docs: add legacy docs README and fix internal refs).
- 2026-01-25 01:25 — Updated codebase map and docs to reference new legacy spec paths; next step verify.
- 2026-01-25 01:25 — Commit c7401c1 (docs: repoint xdsl spec references).
- 2026-01-25 01:26 — Ran `./venv/bin/pytest tests/unit_tests/cli -v`; 10 passed.
- 2026-01-25 01:27 — Commit a386b84 (chore: update T-223 scratchpad).
- 2026-01-25 01:27 — Commit e78532a (chore: log T-223 verification).
- 2026-01-25 01:28 — Opened PR https://github.com/Jianxun/ASDL/pull/230; updated task status to ready_for_review; next step push status change.
- 2026-01-25 01:28 — Ran `./venv/bin/python scripts/lint_tasks_state.py`; OK.
- 2026-01-25 01:28 — Commit 3db9461 (chore: mark T-223 ready for review).
- 2026-01-25 01:29 — Pushed branch updates to origin.
- 2026-01-25 01:32 — Review intake; confirmed PR targets main and verification log present; set status to review_in_progress; next step review diff/scope.
- 2026-01-25 01:33 — Scope review complete; changes match DoD (legacy spec moves + README + ref updates); remaining old-path refs only in scratchpads/tasks.yaml (tasks.yaml locked); proceed to review decision.
- 2026-01-25 01:33 — Posted review-clean PR comment; set status to review_clean; next step merge/closeout.
## Patch summary
- Moved GraphIR/IFIR/NFIR and pipeline specs into `docs/legacy/`.
- Added legacy README and corrected internal doc links.
- Updated codebase map and documentation references to new legacy paths.

## PR URL
https://github.com/Jianxun/ASDL/pull/230

## Verification
 - `./venv/bin/pytest tests/unit_tests/cli -v`
   - Result: pass (10 passed).

## Status request
Ready for review.

## Blockers / Questions
- Remaining references to old `docs/specs` paths exist only in `agents/scratchpads/` and `agents/context/tasks.yaml`; executor role constraints prevent editing those files. Flag for Architect if updates are desired.

## Next steps
- Await review feedback.
- 2026-01-25 01:23 — Task intake; read contract/tasks/status; created scratchpad; set T-223 in_progress; created feature branch; next step inspect docs/specs and references.
