# T-278 - structured instance `parameters`

## Task summary
- Add structured instance object form: `ref` + optional `parameters`.
- Keep inline instance string form backward compatible.
- Reject `params` alias in structured form.

## Verify
- `./venv/bin/pytest tests/unit_tests/ast -v`
