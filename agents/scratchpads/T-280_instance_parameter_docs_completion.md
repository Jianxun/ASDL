# T-280 - docs/completion parity for instance params

## Task summary
- Reuse shared instance parsing in docs and completion helpers.
- Cover structured `parameters` and quoted inline shorthand forms.
- Add regression tests and example coverage for pass-through command params.

## Read
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `src/asdl/ast/instance_expr.py`
- `src/asdl/docs/depgraph.py`
- `src/asdl/docs/render_helpers.py`
- `src/asdl/docs/markdown.py`
- `src/asdl/tools/completion/engine.py`
- `tests/unit_tests/docs/test_depgraph.py`
- `tests/unit_tests/docs/test_markdown.py`
- `tests/unit_tests/tools/test_completion_engine.py`

## Plan
- Add a shared AST helper that parses both inline and structured instance forms.
- Replace docs and completion local instance parsing with the shared helper.
- Add docs/completion regressions for quoted inline command params and structured `parameters`.
- Run the task verify command and capture results.

## Milestone notes
- Intake complete; task moved to `in_progress` and linter passed.
- Implemented shared dual-form instance parsing + inline parameter formatting helper.
- Updated depgraph, markdown, Sphinx render helpers, and completion engine to use shared parser.
- Added regression tests for inline quoted command params and structured `parameters`.

## Verify
- `./venv/bin/pytest tests/unit_tests/docs tests/unit_tests/tools -v`

## Patch summary
- Added `parse_instance_value` + `format_instance_params` in `src/asdl/ast/instance_expr.py`
  to normalize inline shorthand and structured `InstanceDecl` forms.
- Updated docs helpers (`depgraph`, `markdown`, and Sphinx `render_helpers`) to use
  shared parsing and quote-aware parameter formatting.
- Updated completion engine instance parsing to support both string and structured
  instance entries when resolving refs for endpoint/parameter suggestions.
- Added regression tests for:
  - depgraph handling of quoted inline and structured forms
  - markdown rendering parity across both forms
  - completion endpoint suggestions for structured instance declarations

## PR URL
- https://github.com/Jianxun/ASDL/pull/303

## Verification
- `./venv/bin/pytest tests/unit_tests/docs tests/unit_tests/tools -v` (passed; 32 tests)

## Status request
- Done

## Blockers / Questions
- None

## Next steps
- Await reviewer feedback on PR #303.
