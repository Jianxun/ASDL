# T-229: Visualizer Dump CLI

## Goal
Provide `asdlc visualizer-dump` for minimal visualizer JSON via stdout.

## Notes
- Include `--list-modules`, `--module`, `--compact`.
- Emit only what the visualizer needs (no full PatternedGraph dump).
- No files written.
