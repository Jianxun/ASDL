# T-279 - quote-aware inline instance tokenization

## Task summary (DoD + verify)
- Replace whitespace splitting for inline instance params with quote-aware tokenization.
- Support values containing spaces (for example `cmd='.TRAN 0 10u'`).
- Keep named-pattern handling behavior stable.
- Verify command: `./venv/bin/pytest tests/unit_tests/lowering -v`

## Read
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `agents/adr/ADR-0031-instance-parameter-syntax.md`
- `src/asdl/lowering/ast_to_patterned_graph_instances.py`
- `src/asdl/ast/named_patterns.py`
- `src/asdl/tools/completion/engine.py`
- `tests/unit_tests/core/test_patterned_graph_lowering.py`
- `tests/unit_tests/tools/test_completion_engine.py`

## Plan
1. Add a shared quote-aware inline instance tokenizer/parser utility.
2. Rewire lowering/named-pattern/completion helpers to use the shared utility.
3. Add regressions for quoted inline params and named-pattern stability.
4. Run targeted verification and close out task metadata.

## Milestone notes
- Intake complete: T-279 was `ready` and dependencies (T-278) were already `done`.
- Task state moved to `in_progress`; `scripts/lint_tasks_state.py` passed.
- Implemented shared quote-aware tokenization using `shlex` with comments disabled.
- Lowering and completion now parse inline instances through the shared helper.
- Named-pattern instance-param rewriting now tokenizes quote-aware and preserves
  whitespace-bearing values by re-quoting updated values when needed.
- Added tests covering quoted inline values in graph lowering and completion.
- Follow-up on PR #302 reviewer blocker: strict inline parser rejected empty
  quoted values (`key=''`, `key=""`) as malformed tokens.
- Updated strict token validation to allow empty values while still rejecting
  empty keys, restoring pre-refactor token acceptance behavior.
- Added regressions covering empty quoted inline values in lowering/completion
  paths to prevent recurrence.

## Patch summary
- Added `src/asdl/ast/instance_expr.py` with:
  - `tokenize_inline_instance_expr`
  - `parse_inline_instance_expr`
  - `format_inline_param_token`
- Updated `src/asdl/lowering/ast_to_patterned_graph_instances.py` to consume
  the shared strict parser (erroring on malformed param tokens).
- Updated `src/asdl/ast/named_patterns.py` to tokenize instance expressions
  quote-aware and preserve valid inline syntax when rewriting param values.
- Updated `src/asdl/tools/completion/engine.py` to use the shared lenient parser.
- Added regressions in:
  - `tests/unit_tests/core/test_patterned_graph_lowering.py`
  - `tests/unit_tests/tools/test_completion_engine.py`
- Follow-up fix:
  - `src/asdl/ast/instance_expr.py` now treats only missing keys as malformed
    param tokens in strict mode (`key=` is valid; `=value` is invalid).
- Added follow-up regression coverage:
  - `tests/unit_tests/core/test_patterned_graph_lowering.py` verifies quoted
    empty-value tokens no longer trip `IR-001` parsing failures.
  - `tests/unit_tests/tools/test_completion_engine.py` verifies completion still
    resolves params after `cmd=''` and `cmd=""`.

## PR URL
- https://github.com/Jianxun/ASDL/pull/302

## Verification
- `./venv/bin/pytest tests/unit_tests/lowering -v` -> passed (4 tests)
- `./venv/bin/pytest tests/unit_tests/core/test_patterned_graph_lowering.py -v` -> passed (16 tests)
- `./venv/bin/pytest tests/unit_tests/tools/test_completion_engine.py -v` -> passed (4 tests)
- `./venv/bin/python scripts/lint_tasks_state.py` -> passed
- `./venv/bin/pytest tests/unit_tests/core/test_patterned_graph_lowering.py -k "quoted_inline_instance_param_values or empty_quoted_inline_instance_param_tokens" -v` -> passed (2 selected)
- `./venv/bin/pytest tests/unit_tests/tools/test_completion_engine.py -k "quoted_inline_values or empty_quoted_inline_values" -v` -> passed (2 selected)
- `./venv/bin/pytest tests/unit_tests/core/test_patterned_graph_lowering.py -v` -> passed (16 tests)
- `./venv/bin/pytest tests/unit_tests/tools/test_completion_engine.py -v` -> passed (4 tests)

## Status request
- Ready for Review

## Blockers / Questions
- None.

## Next steps
1. Wait for reviewer re-check on PR #302.
