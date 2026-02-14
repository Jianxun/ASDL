# T-275 - asdl-language-tools scaffold

## Task summary (DoD + verify)
- Create a new standalone extension at `extensions/asdl-language-tools/` with no runtime dependency on removed legacy extensions.
- Register ASDL language contributions and wire grammar/snippets in `package.json`.
- Provide a YAML-compatible, net-first ASDL baseline grammar/snippets.
- Verify with:
  - `cd extensions/asdl-language-tools && npm run compile`
  - `./venv/bin/python -c "import yaml, pathlib; yaml.safe_load(pathlib.Path('examples/pdks/gf180mcu/asdl/gf180mcu.asdl').read_text())"`

## Read (paths)
- `agents/roles/executor.md`
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `agents/scratchpads/T-275_asdl_language_tools_scaffold.md`
- `docs/specs/spec_asdl_language_tools_extension.md`

## Plan
1. Create fresh extension package scaffold and TypeScript compile setup.
2. Add language registration, grammar contribution, and snippet contribution in `package.json`.
3. Implement YAML-first TextMate grammar overlays for ASDL-specific keys/tokens.
4. Add net-first ASDL snippets and README.
5. Run required verification commands and prepare closeout.

## Milestone notes
- Created `feature/T-275-asdl-language-tools-scaffold` from `main`.
- Set `T-275` status to `in_progress` and linted task state.
- Implemented a new extension scaffold with no imports from legacy extension packages.
- Grammar design keeps YAML behavior by including `source.yaml` and layering ASDL token scopes on top.

## Patch summary
- Added new package scaffold under `extensions/asdl-language-tools/`:
  - `package.json`, `package-lock.json`, `tsconfig.json`, `.gitignore`
  - `src/extension.ts`
  - `language-configuration.json`
  - `syntaxes/asdl.tmLanguage.json`
  - `snippets/asdl.json`
  - `README.md`
- Updated `agents/context/tasks_state.yaml` status for `T-275` from `ready` to `in_progress`.

## PR URL
- Pending PR creation.

## Verification
- `cd extensions/asdl-language-tools && npm ci && npm run compile` (pass)
- `./venv/bin/python -c "import yaml, pathlib; yaml.safe_load(pathlib.Path('examples/pdks/gf180mcu/asdl/gf180mcu.asdl').read_text()); print('yaml-safe-load-ok')"` (pass)

## Status request
- In Progress

## Blockers / Questions
- None.

## Next steps
- Push feature branch, open PR to `main`, then set task to `ready_for_review` with PR number.
