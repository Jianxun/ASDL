# T-036 - CLI Netlist via MVP Pipeline

## Task summary
- DoD: Implement CLI command under `src/asdl/cli/` that runs the MVP pipeline end-to-end via `src/asdl/ir/pipeline.py` and emits ngspice output (no direct converter calls); expose `--verify` toggle, deterministic diagnostics, and default output `{asdl_basename}.spice`; add CLI-level tests. Blocked on T-034 completion.
- Verify: `pytest tests/unit_tests/cli`

## Read
- `agents/roles/executor.md`
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.md`
- `agents/context/handoff.md`
- `docs/specs_mvp/spec_cli_mvp.md`
- `src/asdl/diagnostics/core.py`
- `src/asdl/diagnostics/renderers.py`
- `src/asdl/diagnostics/collector.py`
- `src/asdl/diagnostics/codes.py`
- `src/asdl/ir/pipeline.py`
- `src/asdl/ast/parser.py`
- `src/asdl/emit/ngspice.py`
- `tests/unit_tests/e2e/test_pipeline_mvp.py`
- `pyproject.toml`

## Plan
- Inspect existing CLI entrypoints, diagnostic utilities, and pipeline entry usage.
- Implement `asdlc netlist` per spec (flags, output naming, verification toggle, top-as-subckt pass-through).
- Add CLI tests for success/error paths and deterministic diagnostics ordering.
- Run `pytest tests/unit_tests/cli` and record results.

## Progress log
- 2026-01-02: Read CLI MVP spec + executor role; switched to `feature/T-036-cli-pipeline`; set T-036 to In Progress.
- 2026-01-02: Implemented click-based `asdlc netlist` CLI, added console script entry, and wrote CLI tests for success/error paths.
- 2026-01-02: Pushed `feature/T-036-cli-pipeline` and opened PR https://github.com/Jianxun/ASDL/pull/31.
- 2026-01-02: Addressed Architect review feedback (stderr assertion + tasks.md placement) and re-ran CLI tests.

## Patch summary
- `src/asdl/cli/__init__.py`: added click CLI group and `netlist` command wired to parser, pipeline, and ngspice emitter.
- `pyproject.toml`: added `asdlc` console script entrypoint.
- `tests/unit_tests/cli/test_netlist.py`: added CLI tests for default output, `--top-as-subckt` + `-o`, and missing input errors.
- `agents/context/codebase_map.md`: noted new `src/asdl/cli/` directory.
- `agents/context/tasks.md`: moved T-036 into Done section.

## PR URL
- https://github.com/Jianxun/ASDL/pull/31

## Verification
- `venv/bin/pytest tests/unit_tests/cli`

## Blockers / Questions
- None.

## Next steps
- Wait for Architect review/approval on PR #31.
