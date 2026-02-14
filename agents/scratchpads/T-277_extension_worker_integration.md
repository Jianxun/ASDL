# T-277 - extension worker integration

## Task summary (DoD + verify)
- Wire VS Code completion provider in `asdl-language-tools` to the Python worker protocol.
- Support document sync and completion request routing.
- Implement graceful fallback structural/snippet completion when worker is unavailable.
- Ensure completion inserts preserve valid YAML structure (keys/list item indentation).
- Verify:
  - `cd extensions/asdl-language-tools && npm test`

## Read
- `agents/roles/executor.md`
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `docs/specs/spec_asdl_language_tools_extension.md`
- `extensions/asdl-language-tools/src/extension.ts`
- `extensions/asdl-language-tools/python/worker.py`
- `src/asdl/tools/completion/engine.py`

## Plan
1. Move `T-277` to `in_progress`; create feature branch.
2. Implement worker client transport (`initialize`, `update_document`, `complete`, `shutdown`).
3. Implement completion provider core with worker routing and fallback suggestions.
4. Integrate provider + document sync in VS Code extension activation.
5. Add TS tests for provider fallback/success and worker client lifecycle.
6. Run `npm test` and prepare closeout.

## Milestone notes
- 2026-02-14: Intake complete; `T-277` set to `in_progress`; task-state lint passed; branch `feature/T-277-extension-worker-integration` created.
- 2026-02-14: Added completion worker client and provider core modules; wired extension activation with worker initialize/sync/deactivate handling.
- 2026-02-14: Added Node test harness and integration tests for provider + worker client; fixed fallback param context and default Python interpreter selection.

## Patch summary
- Added `src/completion/workerClient.ts`:
  - JSON-over-stdio worker protocol client with request timeouts.
  - Worker lifecycle (`initialize`, `updateDocument`, `complete`, `shutdown`).
  - Auto-detect repo `venv/bin/python` and enforce local `PYTHONPATH` to `src/`.
- Added `src/completion/provider.ts`:
  - Worker-backed completion routing.
  - Worker item mapping and YAML-safe fallback suggestions.
- Updated `src/extension.ts`:
  - Register completion provider for `asdl` language.
  - Startup worker initialize + best-effort document sync on open/change.
  - Graceful shutdown in `deactivate` and subscription disposal.
- Added tests:
  - `tests/completion.provider.test.ts`
  - `tests/workerClient.test.ts`
- Added extension test build config/scripts:
  - `tsconfig.tests.json`
  - `package.json` scripts `compile-tests`, `test`.

## PR URL
- Pending.

## Verification
- `cd extensions/asdl-language-tools && npm test` (pass)
  - 5 tests passed: provider mapping, provider fallback, endpoint fallback snippet, worker lifecycle completion round-trip, missing worker-path error.

## Status request
- In Progress

## Blockers / Questions
- None.

## Next steps
1. Commit implementation + tests.
2. Push branch and open PR.
3. Set `T-277` to `ready_for_review` with PR number and re-run task-state lint.
