# Logging System Todo

## Current Sprint (Phase 1: Structured Logging Foundation)

- [ ] Integrate Python logging hierarchy under root `asdlc`
- [ ] Map CLI flags to log levels (`-v`→INFO, `--debug`→DEBUG, `--trace`→TRACE)
- [ ] Replace `click.echo()` progress messages with logger calls (INFO/DEBUG)
- [ ] Implement human-readable formatter with timestamps and component tags
- [ ] Add optional JSON formatter for logs (`--log-json`)
- [ ] Add console handler by default; optional file handler via `--log-file`
- [ ] Respect env vars: `ASDL_LOG_LEVEL`, `ASDL_LOG_FILE`, `ASDL_LOG_FORMAT`
- [ ] Minimal unit tests for logger configuration and flag mapping
- [ ] Integration smoke test: run `asdlc elaborate` with `--debug` and verify output

## Backlog

- [ ] Generate per-run trace ID and propagate in log records
- [ ] Import resolution tracing (search paths, file lookups, alias mapping)
- [ ] Performance timing for pipeline stages
- [ ] Log rotation and file size management
- [ ] Configuration file support (`~/.asdl/config.yaml`)
- [ ] Interactive debug mode scaffolding

## Completed Tasks

- [ ] (none yet)


