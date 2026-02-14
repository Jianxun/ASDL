# T-275 - asdl-language-tools scaffold

## Objective
Create a fresh extension package under `extensions/asdl-language-tools/` with
language registration, syntax grammar, and snippets aligned with net-first ASDL.

## Constraints
- Do not reuse runtime code from removed legacy extension packages.
- Keep grammar YAML-compatible.

## DoD
- New package compiles (`npm run compile`).
- ASDL grammar/snippets exist and are wired in `package.json`.
