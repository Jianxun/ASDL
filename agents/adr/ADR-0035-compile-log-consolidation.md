# ADR-0035: Consolidated Compile Log via `--log` With Default `<entry_file_basename>.log.json`

- Status: Accepted
- Date: 2026-02-23

## Context
ASDL view-binding resolution introduced an inspectable sidecar artifact, and
emission collision handling now benefits from deterministic rename mapping and
warning visibility. Producing multiple separate artifacts increases file
fragmentation and makes CI/debug ingestion harder.

We need a single, stable reporting surface for compile-time outcomes while
keeping machine-readability and deterministic content.

## Decision
Adopt a consolidated compile log artifact for `asdlc netlist`.

1. CLI surface:
   - add `--log <path>` as compile log path override
   - default log path is `<entry_file_basename>.log.json` in the input file
     directory

2. Artifact format:
   - compile log is JSON
   - compile log may contain multiple deterministic sections, including:
     - `view_bindings` (resolved binding entries)
     - `emission_name_map` (logical/base/emitted name mappings)
     - warnings/diagnostics metadata

3. Consolidation policy:
   - compile-time inspection data should be recorded in the consolidated log
     rather than fragmented ad hoc sidecar files

## Consequences
- Positive: one canonical run artifact simplifies CI collection, debugging, and
  reproducibility.
- Positive: related compile metadata (bindings, renames, warnings) remains
  co-located and easier to diff.
- Tradeoff: larger single file versus smaller specialized files.

## Alternatives
- Keep separate sidecar files per subsystem (for example bindings vs name map):
  rejected due to fragmentation and higher orchestration overhead.
- Text-only logs: rejected because structured JSON is better for tool-driven
  validation and deterministic diffing.
