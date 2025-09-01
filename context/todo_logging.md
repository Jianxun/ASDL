# Logging System Todo

## Current Sprint (Phase 1: Structured Logging Foundation)

- [X] Integrate Python logging hierarchy under root `asdlc`
- [X] Map CLI flags to log levels (`-v`→INFO, `--debug`→DEBUG, `--trace`→TRACE)
- [X] Replace `click.echo()` progress messages with logger calls (INFO/DEBUG)
- [X] Implement human-readable formatter with timestamps and component tags
- [X] Add optional JSON formatter for logs (`--log-json`)
- [X] Add console handler by default; optional file handler via `--log-file`
- [X] Respect env vars: `ASDL_LOG_LEVEL`, `ASDL_LOG_FILE`, `ASDL_LOG_FORMAT`
- [ ] Minimal unit tests for logger configuration and flag mapping
- [X] Minimal unit tests for logger configuration and flag mapping
- [X] Integration smoke test: run CLI with `--debug/--trace` and verify output levels

## Backlog

- [ ] Generate per-run trace ID and propagate in log records
- [ ] Import resolution tracing (search paths, file lookups, alias mapping)
- [ ] Performance timing for pipeline stages
- [ ] Log rotation and file size management
- [ ] Configuration file support (`~/.asdl/config.yaml`)
- [ ] Interactive debug mode scaffolding

## Completed Tasks

- [X] Phase 1 foundation implemented in CLI and logging utils


