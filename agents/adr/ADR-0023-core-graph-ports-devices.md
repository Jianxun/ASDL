# ADR-0023: Core Graph Ports and Device Definitions

Status: Accepted

## Context
Atomized/Patterned graphs are used by verification and emission. Today they only
carry module port_order and no device definitions, which forces port validation
and emission to rely on AST/ProgramDB or sidecar registries. We want ports to be
first-class in the core graphs while keeping those graphs backend-agnostic.

## Decision
- Add first-class device definitions to core graphs (ProgramGraph and
  AtomizedProgramGraph) as leaf nodes with stable IDs, names, file_id, ports
  list, and optional attrs/parameters/variables.
- Replace module `port_order` with `ports` and require `ports` to be a list
  everywhere (empty list allowed, never None).
- Keep backend templates/config out of core graph dataclasses; backend lowering
  resolves templates from backend config using device definitions.

## Consequences
- Verifiers can validate endpoint ports using only core graphs.
- Lowering/builders must always provide `ports` lists (no None handling).
- Backend emission remains decoupled from graph semantics; template lookup stays
  in backend passes.

## Alternatives
- Keep device defs in a registry or ProgramDB sidecar; rejected because ports
  must be first-class for verification/emission.
- Store backend templates in core graphs; rejected to keep core graphs
  backend-agnostic and avoid duplicating backend config.
