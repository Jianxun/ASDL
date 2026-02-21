# T-279 - quote-aware inline instance tokenization

## Task summary
- Replace whitespace splitting for inline instance params with quote-aware tokenization.
- Support values containing spaces (for example `cmd='.TRAN 0 10u'`).
- Keep named-pattern handling behavior stable.

## Verify
- `./venv/bin/pytest tests/unit_tests/lowering -v`
