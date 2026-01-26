# T-230: Extension runs asdlc visualizer-dump + module selection

## Task summary (DoD + verify)
- DoD: Replace dump file selection with `asdlc visualizer-dump` invoked via PATH. If multiple modules exist, prompt via QuickPick and re-run with `--module`. Parse minimal JSON and feed the webview. Surface friendly errors when `asdlc` is missing or the command fails. No dumps are written to disk.
- Verify: `npm run build`

## Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `agents/roles/executor.md`

## Plan
- Review current visualizer extension dump flow and command execution.
- Update extension logic to call `asdlc visualizer-dump`, handle module listing/prompt, and parse JSON into webview payload.
- Add error handling for missing/failed CLI and ensure no dump files are written.
- Run `npm run build` and record results.

## Progress log
- 2026-01-26 00:52 — Task intake; read executor workflow + project context; set task status to in_progress; created feature branch; updated scratchpad; next step: update visualizer extension to call asdlc visualizer-dump.

## Patch summary
- Pending.

## PR URL
- Pending.

## Verification
- Pending.

## Status request
- In Progress.

## Blockers / Questions
- None.

## Next steps
- Update extension to invoke `asdlc visualizer-dump` and map JSON to webview payload.
