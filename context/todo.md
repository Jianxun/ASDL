# Unified Todo Redirect

The original combined todo list has been split for clarity. Please refer to the new focused files:

## Active Development (Priority Order)
- `context/todo_imports.md` – **🚀 PHASE 1.2 READY** - Import system as elaborator phase (P0503, E0441-E0445)
- `context/todo_parameter_system.md` – **✅ COMPLETED** - Parameter resolving system enhancement
- `context/todo_compiler.md` – Compiler / CLI pipeline tasks
- `context/todo_cli.md` – CLI implementation and testing tasks
- `context/todo_visualizer.md` – Front-end visualizer work
- `context/todo_schema.md` – Schema generation system tasks
  - Note: Reflect enum rename `SignalType` → `PortType` and removal of `PortConstraints` in schema docs

## Planning & Backlog
- `context/backlog_validation.md` – Validation & DRC backlog
- `context/backlog_ux.md` – UX & documentation backlog

## Archive & Reference
- `context/done.md` – Archive of completed milestones
- `context/todo_legacy_archive.md` – Historical todo archive

## Next Session
- Continue updating any remaining unit tests under `tests/unit_tests/data_structures/` to align with `PortType` and removed `PortConstraints`.
- Run unit tests only (skip integration) until refactor completes.

## Documentation Reference
- `doc/cli/` – CLI architecture and implementation plans