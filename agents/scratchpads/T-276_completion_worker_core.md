# T-276 - completion worker core

## Objective
Implement a long-lived Python completion worker that reuses ASDL parser/import
and `.asdlrc` config semantics for endpoint, import symbol, and `param=`
completion suggestions.

## Constraints
- Reuse `src/asdl/ast/*`, `src/asdl/imports/*`, `src/asdl/cli/config.py`.
- Stable JSON message protocol: initialize/update_document/complete/shutdown.

## DoD
- Unit tests validate completion categories and request lifecycle.
