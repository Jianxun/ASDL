# T-280 - docs/completion parity for instance params

## Task summary
- Reuse shared instance parsing in docs and completion helpers.
- Cover structured `parameters` and quoted inline shorthand forms.
- Add regression tests and example coverage for pass-through command params.

## Verify
- `./venv/bin/pytest tests/unit_tests/docs tests/unit_tests/tools -v`
